/*
 * Mew Assistant - the three persona screens.
 *
 * Deliberately small and framework-free, matching the rest of app/templates.
 * The prototype's runtime (support.js in the design bundle) is not ported;
 * this talks to the real API instead.
 *
 * Two rules this file exists to keep:
 *   1. No client decides whether a change is allowed. Every ask is a POST to
 *      /requests (or /kid/ask), and the response says what happened.
 *   2. Nothing is announced in a single channel. Every banner, confetti burst
 *      and spoken line also lands in the live region as the same sentence.
 */
(function (global) {
  'use strict';

  var TOKEN_KEY = 'mew_token';

  // ------------------------------------------------------------ strings

  function lookup(path) {
    var node = global.MEW.strings;
    var parts = path.split('.');
    for (var i = 0; i < parts.length; i++) {
      if (node == null || typeof node !== 'object' || !(parts[i] in node)) return path;
      node = node[parts[i]];
    }
    return node;
  }

  function t(path, params) {
    var template = lookup(path);
    if (template && typeof template === 'object') {
      // Plural forms: { one, other }
      template = (params && params.count === 1) ? template.one : template.other;
    }
    if (typeof template !== 'string') return String(template);
    if (!params) return template;
    return Object.keys(params).reduce(function (out, name) {
      return out.split('{' + name + '}').join(String(params[name]));
    }, template);
  }

  // ------------------------------------------------------- formatting

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  function timeLabel(date) {
    if (global.MEW.clock === '24h') return pad(date.getHours()) + ':' + pad(date.getMinutes());
    var hour = date.getHours() % 12 || 12;
    var suffix = date.getHours() < 12 ? 'am' : 'pm';
    return hour + (date.getMinutes() ? ':' + pad(date.getMinutes()) : '') + suffix;
  }

  function dayName(date) {
    // Mon=0, matching the rule engine and the locale's day list.
    return lookup('days')[(date.getDay() + 6) % 7];
  }

  /** Format an "HH:MM[:SS]" wall-clock string the way this locale reads it. */
  function clockLabel(value, fallback) {
    var raw = value || fallback;
    if (!raw) return '';
    var parts = String(raw).split(':');
    var probe = new Date();
    probe.setHours(Number(parts[0]) || 0, Number(parts[1]) || 0, 0, 0);
    return timeLabel(probe);
  }

  // ------------------------------------------------------------- DOM

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (name) {
      if (name === 'class') node.className = attrs[name];
      else if (name === 'text') node.textContent = attrs[name];
      else if (name.indexOf('on') === 0) node.addEventListener(name.slice(2), attrs[name]);
      else if (attrs[name] !== null && attrs[name] !== undefined) {
        node.setAttribute(name, attrs[name]);
      }
    });
    (children || []).forEach(function (child) {
      if (child) node.appendChild(child);
    });
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /**
   * Say something once, in every channel at once: on screen, to the screen
   * reader, and - only if read-aloud is on - out loud as the same sentence.
   */
  function announce(text, speakIt) {
    var live = document.getElementById('mew-live');
    if (live) live.textContent = text;
    if (speakIt) speak(text);
  }

  function speak(text) {
    try {
      var synth = global.speechSynthesis;
      if (!synth) return;
      synth.cancel();
      var utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.92;
      utterance.lang = global.MEW.locale;
      synth.speak(utterance);
    } catch (error) { /* speech is an addition, never the only channel */ }
  }

  // -------------------------------------------------------------- api

  function token() {
    try { return global.localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }

  function api(path, options) {
    options = options || {};
    var headers = { 'Accept-Language': global.MEW.locale };
    if (options.body) headers['Content-Type'] = 'application/json';
    if (token()) headers.Authorization = 'Bearer ' + token();
    return fetch(path, {
      method: options.method || 'GET',
      headers: headers,
      body: options.body ? JSON.stringify(options.body) : undefined
    }).then(function (response) {
      if (response.status === 401 || response.status === 403) {
        requireSignIn();
        throw new Error('unauthenticated');
      }
      if (!response.ok) throw new Error('http ' + response.status);
      return response.status === 204 ? null : response.json();
    });
  }

  /** A token gate, not a product screen: real sign-in lives in /auth. */
  function requireSignIn() {
    if (document.getElementById('mew-signin')) return;
    var input = el('input', { id: 'mew-token', type: 'password',
                              placeholder: t('ui.token'), autocomplete: 'off' });
    var form = el('form', {
      id: 'mew-signin', class: 'signin',
      onsubmit: function (event) {
        event.preventDefault();
        try { global.localStorage.setItem(TOKEN_KEY, input.value.trim()); } catch (e) { /* private mode */ }
        global.location.reload();
      }
    }, [
      el('h2', { text: t('ui.sign_in'), style: 'font-size:17px;font-weight:600' }),
      input,
      el('button', { class: 'btn btn--primary', type: 'submit', text: t('ui.continue') })
    ]);
    document.querySelector('.page').insertBefore(form, document.querySelector('.page').firstChild);
  }

  function failed(node) {
    clear(node);
    node.appendChild(el('p', { class: 'empty', text: t('ui.error') }));
  }

  // ----------------------------------------------------------- parent

  var parent = {
    state: { tab: 'inbox' },

    start: function () {
      Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (tab) {
        tab.addEventListener('click', function () { parent.show(tab.dataset.pane); });
      });
      parent.load();
    },

    show: function (pane) {
      parent.state.tab = pane;
      Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (tab) {
        tab.setAttribute('aria-selected', String(tab.dataset.pane === pane));
      });
      ['inbox', 'week', 'rules'].forEach(function (name) {
        document.getElementById('pane-' + name).hidden = name !== pane;
      });
      if (pane === 'week') parent.loadWeek();
      if (pane === 'rules') parent.loadRules();
    },

    load: function () {
      var inbox = document.getElementById('parent-inbox');
      api('/parent/approvals/inbox').then(function (requests) {
        parent.renderInbox(requests);
        document.getElementById('parent-count').textContent = requests.length
          ? t('parent.waiting', { count: requests.length })
          : t('parent.all_clear');
      }).catch(function () { failed(inbox); });

      api('/parent/log?limit=8').then(parent.renderLog).catch(function () {});
    },

    renderInbox: function (requests) {
      var host = document.getElementById('parent-inbox');
      clear(host);
      if (!requests.length) {
        host.appendChild(el('p', { class: 'empty', text: t('parent.nothing_waiting') }));
        return;
      }
      requests.forEach(function (request) {
        host.appendChild(parent.card(request));
      });
    },

    card: function (request) {
      var options = (request.alternatives || []).map(function (option) {
        return el('button', {
          class: 'option', type: 'button',
          onclick: function () { parent.choose(request.id, option.index); }
        }, [
          el('span', { class: 'option__label', text: option.label }),
          el('span', { class: 'option__note', text: option.note })
        ]);
      });

      var body = [
        el('p', { class: 'request-card__source', text: request.source_label }),
        el('h3', { class: 'request-card__headline', text: request.headline }),
        el('p', { class: 'request-card__detail', text: request.detail })
      ];

      if (request.reasons_text) {
        body.push(el('p', { class: 'request-card__reason', text: request.reasons_text }));
      }
      if (options.length) {
        body.push(el('p', { class: 'request-card__pick', text: t('parent.pick_fit') }));
        options.forEach(function (option) { body.push(option); });
      }

      var isCancel = request.kind === 'cancel';
      body.push(el('div', { class: 'actions' }, [
        el('button', {
          class: 'btn btn--primary', type: 'button',
          text: isCancel ? t('parent.skip_it') : t('parent.allow_anyway'),
          onclick: function () { parent.approve(request.id); }
        }),
        el('button', {
          class: 'btn btn--quiet', type: 'button', text: t('parent.say_no'),
          onclick: function () { parent.deny(request.id); }
        })
      ]));

      return el('article', { class: 'request-card' }, body);
    },

    choose: function (requestId, index) {
      api('/parent/approvals/' + requestId + '/choose', {
        method: 'POST', body: { alternative_index: index }
      }).then(function (result) {
        announce(t('parent.meta_picked') + ' · ' + result.when);
        parent.load();
      }).catch(function () { announce(t('ui.error')); });
    },

    approve: function (requestId) {
      api('/parent/approvals/' + requestId + '/approve', {
        method: 'POST', body: { approved: true }
      }).then(function () { parent.load(); })
        .catch(function () { announce(t('ui.error')); });
    },

    // A denial requires a note - that is an API rule, and a kindness.
    deny: function (requestId) {
      var note = global.prompt(t('parent.say_no'));
      if (!note) return;
      api('/parent/approvals/' + requestId + '/deny', {
        method: 'POST', body: { approved: false, parent_note: note }
      }).then(function () { parent.load(); })
        .catch(function () { announce(t('ui.error')); });
    },

    renderLog: function (entries) {
      var host = document.getElementById('parent-log');
      clear(host);
      if (!entries.length) {
        host.appendChild(el('p', { class: 'log-row__meta', text: t('parent.no_changes') }));
        return;
      }
      entries.forEach(function (entry) {
        host.appendChild(el('div', {
          class: 'log-row' + (entry.tone === 'manual' ? ' log-row--manual' : '')
        }, [
          el('span', { class: 'log-row__dot', 'aria-hidden': 'true' }),
          el('div', {}, [
            el('p', { class: 'log-row__text', text: entry.text }),
            el('p', { class: 'log-row__meta', text: entry.meta })
          ])
        ]));
      });
    },

    loadWeek: function () {
      var host = document.getElementById('pane-week');
      api('/parent/week').then(function (days) {
        clear(host);
        days.forEach(function (day) {
          var rows = day.sessions.map(function (session) {
            var children = [
              el('span', { class: 'session-row__rail', 'aria-hidden': 'true' }),
              el('div', { class: 'session-row__body' }, [
                el('p', { class: 'session-row__title', text: session.title }),
                el('p', {
                  class: 'session-row__meta',
                  text: session.time_label + ' · ' + (session.provider_person_name || '')
                })
              ])
            ];
            if (session.changed) {
              children.push(el('span', { class: 'pill', text: t('parent.updated') }));
            }
            return el('div', { class: 'session-row' }, children);
          });
          if (day.empty) {
            rows.push(el('p', { class: 'day__free', text: t('parent.free') }));
          }
          host.appendChild(el('section', { class: 'day' }, [
            el('div', { class: 'day__head' }, [
              el('h3', { class: 'day__name', text: day.name }),
              el('span', { class: 'day__date', text: day.label })
            ])
          ].concat(rows)));
        });
      }).catch(function () { failed(host); });
    },

    loadRules: function () {
      var host = document.getElementById('parent-rules');
      api('/rules').then(function (rules) { parent.renderRules(host, rules); })
        .catch(function () { failed(host); });
    },

    /**
     * Six toggles, first person and concrete. Each row maps to exactly one
     * field on the rule set; turning a row off sends null, which is what an
     * inactive rule means to the engine.
     */
    renderRules: function (host, rules) {
      clear(host);
      var block = (rules.protected_blocks || [])[0];

      var rows = [
        {
          key: 'min_notice',
          on: rules.min_notice_hours !== null && rules.min_notice_hours !== undefined,
          params: { hours: rules.min_notice_hours || 24 },
          patch: function (on) { return { min_notice_hours: on ? 24 : null }; }
        },
        {
          key: 'latest_end',
          on: !!rules.latest_end,
          params: { time: clockLabel(rules.latest_end, '18:00') },
          patch: function (on) { return { latest_end: on ? '18:00:00' : null }; }
        },
        {
          key: 'protected_block',
          on: !!block,
          params: {
            start: clockLabel(block && block.start, '12:00'),
            end: clockLabel(block && block.end, '13:00')
          },
          patch: function (on) {
            return {
              protected_blocks: on
                ? [{ start: '12:00:00', end: '13:00:00', label_key: 'block.midday' }]
                : []
            };
          }
        },
        {
          key: 'same_provider',
          on: !!rules.require_same_provider_person,
          params: {},
          patch: function (on) { return { require_same_provider_person: on }; }
        },
        {
          key: 'buffer',
          on: rules.buffer_minutes !== null && rules.buffer_minutes !== undefined,
          params: { minutes: rules.buffer_minutes || 45 },
          patch: function (on) { return { buffer_minutes: on ? 45 : null }; }
        },
        {
          key: 'cancel_needs_approval',
          on: !!rules.cancellation_needs_approval,
          params: {},
          patch: function (on) { return { cancellation_needs_approval: on }; }
        }
      ];

      rows.forEach(function (row) {
        var button = el('button', {
          class: 'rule-row', type: 'button', 'aria-pressed': String(row.on),
          onclick: function () {
            var next = button.getAttribute('aria-pressed') !== 'true';
            api('/rules', { method: 'PUT', body: row.patch(next) })
              .then(function (updated) { parent.renderRules(host, updated); })
              .catch(function () { announce(t('ui.error')); });
          }
        }, [
          el('span', { class: 'rule-row__body' }, [
            el('span', { class: 'rule-row__label', text: t('parent.rules.' + row.key + '.label', row.params) }),
            el('span', { class: 'rule-row__detail', text: t('parent.rules.' + row.key + '.detail', row.params) })
          ]),
          // The word is the status. The switch is the picture of it.
          el('span', { class: 'rule-row__state', text: row.on ? t('parent.rules.on') : t('parent.rules.off') }),
          el('span', { class: 'switch', 'aria-hidden': 'true' }, [
            el('span', { class: 'switch__knob' })
          ])
        ]);
        host.appendChild(button);
      });
    }
  };

  // -------------------------------------------------------------- kid

  var kid = {
    state: { symbols: false, readAloud: false, busy: {} },

    start: function () {
      document.getElementById('mode-words').addEventListener('click', function () {
        kid.setMode(false);
      });
      document.getElementById('mode-symbols').addEventListener('click', function () {
        kid.setMode(true);
      });
      document.getElementById('mode-read').addEventListener('click', function () {
        kid.state.readAloud = !kid.state.readAloud;
        document.getElementById('mode-read').setAttribute('aria-pressed', String(kid.state.readAloud));
        kid.load();
      });
      kid.load();
    },

    setMode: function (symbols) {
      kid.state.symbols = symbols;
      document.getElementById('mode-words').setAttribute('aria-pressed', String(!symbols));
      document.getElementById('mode-symbols').setAttribute('aria-pressed', String(symbols));
      kid.load();
    },

    load: function () {
      var host = document.getElementById('kid-cards');
      api('/kid/today').then(function (today) {
        document.getElementById('kid-day').textContent = today.day_label;
        document.getElementById('kid-count').textContent = today.count_label;
        document.getElementById('kid-streak').textContent = today.streak_label;

        var dots = document.getElementById('kid-dots');
        clear(dots);
        today.cards.forEach(function () { dots.appendChild(el('span', { class: 'kid-dot' })); });

        clear(host);
        today.cards.forEach(function (card) { host.appendChild(kid.card(card)); });
      }).catch(function () { failed(host); });
    },

    card: function (card) {
      var body = [
        el('h3', { class: 'kid-card__title', text: card.title }),
        el('p', { class: 'kid-card__time', text: card.time_label })
      ];
      if (card.person) {
        body.push(el('p', { class: 'kid-card__who', text: t('kid.with') + ' ' + card.person }));
      }
      if (kid.state.symbols) {
        body.push(el('div', { class: 'kid-symbols' }, card.symbols.map(function (symbol) {
          return el('span', {
            class: 'kid-symbol', text: symbol.glyph, title: t(symbol.label_key),
            'aria-label': t(symbol.label_key), role: 'img'
          });
        })));
      }

      var sentence = card.title + '. ' + card.time_label +
        (card.person ? '. ' + t('kid.with') + ' ' + card.person : '');

      var top = [
        el('span', { class: 'kid-tile kid-tile--' + card.tile_index, 'aria-hidden': 'true',
                     text: card.initial }),
        el('div', { class: 'kid-card__body' }, body)
      ];
      if (kid.state.readAloud) {
        top.push(el('button', {
          class: 'speak', type: 'button', text: '♪',
          'aria-label': t('kid.read_aloud'),
          onclick: function () { announce(sentence, true); }
        }));
      }

      var children = [el('div', { class: 'kid-card__top' }, top)];

      if (card.status_text) {
        // While a request is open the buttons are replaced, never moved.
        children.push(el('p', { class: 'kid-status', text: card.status_text }));
      } else if (card.can_ask) {
        children.push(el('div', { class: 'kid-actions' }, [
          el('button', {
            class: 'kid-btn kid-btn--later', type: 'button', text: t('kid.ask_later'),
            'aria-label': t('kid.ask_later'),
            onclick: function () { kid.ask(card, 'later'); }
          }),
          el('button', {
            class: 'kid-btn kid-btn--skip', type: 'button', text: t('kid.ask_skip'),
            'aria-label': t('kid.ask_skip'),
            onclick: function () { kid.ask(card, 'skip'); }
          })
        ]));
      }

      return el('article', { class: 'kid-card' }, children);
    },

    ask: function (card, what) {
      if (kid.state.busy[card.session_id]) return;
      kid.state.busy[card.session_id] = true;

      api('/kid/ask', { method: 'POST', body: { session_id: card.session_id, ask: what } })
        .then(function (result) {
          kid.state.busy[card.session_id] = false;
          kid.banner(result.message, result.auto_applied);
          kid.load();
        })
        .catch(function () {
          kid.state.busy[card.session_id] = false;
          kid.banner(t('ui.error'), false);
        });
    },

    /** Banner + live region + optional speech. Never colour alone. */
    banner: function (message, done) {
      var host = document.getElementById('kid-banner');
      clear(host);

      var children = [];
      if (done) {
        children.push(el('div', { class: 'confetti', 'aria-hidden': 'true' },
          [0, 1, 2, 3, 4, 5].map(function (index) {
            return el('span', { style: 'animation-delay:' + (index * 0.09) + 's' });
          })));
      }
      children.push(el('p', { text: message }));

      host.appendChild(el('div', {
        class: 'banner ' + (done ? 'banner--done' : 'banner--waiting')
      }, children));

      announce(message, kid.state.readAloud);
      if (global.navigator && global.navigator.vibrate) {
        try { global.navigator.vibrate(done ? [18, 40, 18] : 24); } catch (e) { /* optional */ }
      }
    }
  };

  // --------------------------------------------------------- provider

  var provider = {
    state: { open: null, draft: {} },

    start: function () { provider.load(); },

    load: function () {
      var host = document.getElementById('provider-sessions');
      api('/provider/sessions').then(function (rows) {
        clear(host);
        if (!rows.length) {
          host.appendChild(el('p', { class: 'empty', text: t('parent.no_changes') }));
          return;
        }
        rows.forEach(function (row) { host.appendChild(provider.row(row)); });
      }).catch(function () { failed(host); });
    },

    row: function (row) {
      var session = row.session;
      var open = provider.state.open === session.id;

      var head = el('button', {
        class: 'provider-session__head', type: 'button', 'aria-expanded': String(open),
        onclick: function () {
          provider.state.open = open ? null : session.id;
          if (!open) provider.draft(session);
          provider.load();
        }
      }, [
        el('div', {}, [
          el('p', { class: 'provider-session__when', text: row.when_label }),
          el('p', {
            class: 'provider-session__meta',
            text: session.title + ' · ' + (session.provider_person_name || '')
          })
        ]),
        el('span', {
          class: 'provider-session__action',
          text: row.waiting_on_parent
            ? t('provider.waiting_on_parent')
            : (open ? t('provider.close') : t('provider.change_this'))
        })
      ]);

      var children = [head];
      if (open && !row.waiting_on_parent) {
        children.push(provider.form(row));
      }
      return el('div', { class: 'provider-session' }, children);
    },

    draft: function (session) {
      var start = new Date(session.start_utc);
      provider.state.draft = {
        date: start,
        minutes: start.getHours() * 60 + start.getMinutes(),
        personId: session.provider_person_id
      };
    },

    form: function (row) {
      var session = row.session;
      var draft = provider.state.draft;

      // Five weekdays from today, and half-hour starts across the working day:
      // fixed chips, so a provider never has to type a time.
      var days = [];
      for (var offset = 0; offset < 5; offset++) {
        var date = new Date();
        date.setDate(date.getDate() + offset);
        date.setHours(0, 0, 0, 0);
        days.push(date);
      }
      var times = [];
      for (var minutes = 8 * 60; minutes <= 17 * 60; minutes += 60) times.push(minutes);

      var dayChips = days.map(function (date) {
        var selected = draft.date && draft.date.toDateString() === date.toDateString();
        return el('button', {
          class: 'chip', type: 'button', 'aria-pressed': String(selected),
          text: dayName(date),
          onclick: function () { draft.date = date; provider.load(); }
        });
      });

      var timeChips = times.map(function (minutes) {
        var probe = new Date();
        probe.setHours(Math.floor(minutes / 60), minutes % 60, 0, 0);
        return el('button', {
          class: 'chip', type: 'button', 'aria-pressed': String(draft.minutes === minutes),
          text: timeLabel(probe),
          onclick: function () { draft.minutes = minutes; provider.load(); }
        });
      });

      var roster = row.people || [];
      var current = roster.filter(function (person) { return person.id === draft.personId; })[0];
      var swapped = draft.personId !== session.provider_person_id;

      var therapist = el('button', {
        class: 'therapist-row' + (swapped ? ' therapist-row--swapped' : ''),
        type: 'button',
        onclick: function () {
          if (roster.length < 2) return;
          var index = roster.map(function (p) { return p.id; }).indexOf(draft.personId);
          draft.personId = roster[(index + 1) % roster.length].id;
          provider.load();
        }
      }, [
        el('span', { text: t('provider.person') + ' ' + (current ? current.display_name : '') }),
        el('span', { class: 'option__note', text: t('provider.tap_to_swap') })
      ]);

      return el('div', { class: 'provider-session__form' }, [
        el('div', {}, [
          el('p', { class: 'field-label', text: t('provider.move_to') }),
          el('div', { class: 'chips' }, dayChips)
        ]),
        el('div', {}, [
          el('p', { class: 'field-label', text: t('provider.start_at') }),
          el('div', { class: 'chips' }, timeChips)
        ]),
        therapist,
        el('button', {
          class: 'btn--send', type: 'button', text: t('provider.send'),
          onclick: function () { provider.send(session, swapped); }
        }),
        el('p', { class: 'provider-note', text: t('provider.note') })
      ]);
    },

    send: function (session, swapped) {
      var draft = provider.state.draft;
      var start = new Date(draft.date.getTime());
      start.setHours(Math.floor(draft.minutes / 60), draft.minutes % 60, 0, 0);

      api('/requests', {
        method: 'POST',
        body: {
          session_id: session.id,
          kind: swapped ? 'swap_provider' : 'move',
          new_start: start.toISOString(),
          new_provider_person_id: swapped ? draft.personId : null
        }
      }).then(function (result) {
        provider.banner(result.message, result.auto_applied);
        provider.state.open = null;
        provider.load();
      }).catch(function () { provider.banner(t('ui.error'), false); });
    },

    /** States which of the two things happened, in words, immediately. */
    banner: function (message, applied) {
      var host = document.getElementById('provider-banner');
      clear(host);
      host.appendChild(el('p', {
        class: 'provider-banner ' + (applied ? 'provider-banner--ok' : 'provider-banner--sent'),
        text: message
      }));
      announce(message);
    }
  };

  global.Mew = { t: t, api: api, parent: parent, kid: kid, provider: provider, announce: announce };
})(window);
