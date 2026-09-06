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

  /**
   * The session lives in an HttpOnly cookie, so this page cannot read it and
   * neither can anything injected into it. Requests carry it automatically;
   * a 401 means it expired or was never set, and the answer is the sign-in
   * screen rather than a box asking for a pasted token.
   */
  function api(path, options) {
    options = options || {};
    var headers = { 'Accept-Language': global.MEW.locale };
    if (options.body) headers['Content-Type'] = 'application/json';
    return fetch(path, {
      method: options.method || 'GET',
      headers: headers,
      credentials: 'same-origin',
      body: options.body ? JSON.stringify(options.body) : undefined
    }).then(function (response) {
      if (response.status === 401) {
        requireSignIn();
        throw new Error('unauthenticated');
      }
      if (!response.ok) {
        return response.json().catch(function () { return null; }).then(function (body) {
          var err = new Error((body && body.detail) || ('http ' + response.status));
          err.status = response.status;
          err.detail = body && body.detail;
          throw err;
        });
      }
      return response.status === 204 ? null : response.json();
    });
  }

  function requireSignIn() {
    var here = global.location.pathname + global.location.search;
    global.location.assign('/app/sign-in?next=' + encodeURIComponent(here));
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
      // The Google Calendar connect flow redirects back here with
      // ?tab=providers so the parent lands where they left off.
      var requested = new URLSearchParams(global.location.search).get('tab');
      if (requested && requested !== 'inbox') parent.show(requested);
    },

    show: function (pane) {
      parent.state.tab = pane;
      Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (tab) {
        tab.setAttribute('aria-selected', String(tab.dataset.pane === pane));
      });
      ['inbox', 'week', 'rules', 'providers'].forEach(function (name) {
        document.getElementById('pane-' + name).hidden = name !== pane;
      });
      if (pane === 'week') parent.loadWeek();
      if (pane === 'rules') parent.loadRules();
      if (pane === 'providers') parent.loadProviders();
    },

    /**
     * "Parent" and "guardian" are the same persona. The family's own word
     * comes back with their rules, so the label corrects itself on load
     * rather than making anyone read the wrong one.
     */
    applyCaregiverTerm: function (rules) {
      if (!rules || !rules.caregiver_label) return;
      var panel = document.getElementById('parent-panel');
      var label = document.getElementById('parent-persona');
      var name = document.getElementById('parent-name');
      var previous = panel ? panel.getAttribute('data-caregiver-term') : null;

      if (label) label.textContent = rules.caregiver_label;
      if (panel) {
        panel.setAttribute('aria-label', rules.caregiver_label);
        panel.setAttribute('data-caregiver-term', rules.caregiver_term);
      }
      // Only replace the heading if it is still the placeholder word, never
      // a name the family typed.
      if (name && previous && name.textContent === t('persona.' + previous)) {
        name.textContent = rules.caregiver_label;
      }
    },

    load: function () {
      var inbox = document.getElementById('parent-inbox');
      api('/rules').then(parent.applyCaregiverTerm).catch(function () {});
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
      api('/rules').then(function (rules) {
        parent.applyCaregiverTerm(rules);
        parent.renderRules(host, rules);
      }).catch(function () { failed(host); });
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
    },

    loadProviders: function () {
      var host = document.getElementById('parent-providers');
      var chooseOrgId = Number(new URLSearchParams(global.location.search).get('choose_calendar_org'));
      api('/calendar-sync/orgs').then(function (orgs) {
        parent.renderProviders(host, orgs, chooseOrgId);
      }).catch(function () { failed(host); });

      parent.loadKidCalendars();
    },

    renderProviders: function (host, orgs, chooseOrgId) {
      clear(host);
      if (!orgs.length) {
        host.appendChild(el('p', { class: 'empty', text: t('parent.no_providers') }));
      } else {
        orgs.forEach(function (org) { host.appendChild(parent.providerCard(org, chooseOrgId)); });
      }
      host.appendChild(parent.addProviderForm());
    },

    // A family's roster of providers grows over time - the setup wizard
    // only ever runs once, so this is the only way to add a second (or
    // fifth) provider afterward.
    addProviderForm: function () {
      var nameInput = el('input', { type: 'text', placeholder: t('parent.add_provider_name_placeholder') });
      var kindSelect = el('select', {}, [
        el('option', { value: 'aba', text: t('parent.kind_aba') }),
        el('option', { value: 'speech', text: t('parent.kind_speech') }),
        el('option', { value: 'ot', text: t('parent.kind_ot') }),
        el('option', { value: 'school', text: t('parent.kind_school') }),
        el('option', { value: 'transport', text: t('parent.kind_transport') }),
        el('option', { value: 'other', text: t('parent.kind_other') })
      ]);
      kindSelect.value = 'other';
      var statusMsg = el('p', { class: 'log-row__meta' });
      var addBtn = el('button', {
        class: 'btn btn--primary', type: 'button', text: t('parent.add_provider'),
        onclick: function () {
          var name = (nameInput.value || '').trim();
          if (!name) return;
          statusMsg.textContent = t('ui.loading');
          api('/onboarding/providers', { method: 'POST', body: { name: name, kind: kindSelect.value } })
            .then(function () {
              nameInput.value = '';
              parent.loadProviders();
            })
            .catch(function () { statusMsg.textContent = t('ui.error'); });
        }
      });
      return el('article', { class: 'provider-card' }, [
        el('p', { class: 'field-label', text: t('parent.add_provider_heading') }),
        el('div', { class: 'actions' }, [nameInput, kindSelect, addBtn]),
        statusMsg
      ]);
    },

    providerCard: function (org, chooseOrgId) {
      var statusMsg = el('p', { class: 'log-row__meta' });

      var statusText = org.calendar_connected
        ? (org.calendar_display_name
          ? t('parent.calendar_connected_named', { name: org.calendar_display_name, provider: org.calendar_provider })
          : t('parent.calendar_connected', { provider: org.calendar_provider }))
        : t('parent.calendar_not_connected');

      var icsInput = el('input', { type: 'text', placeholder: t('parent.ics_url_placeholder') });
      var connectIcsBtn = el('button', {
        class: 'btn btn--quiet', type: 'button', text: t('parent.connect_ics'),
        onclick: function () { parent.connectIcs(org.id, icsInput.value, statusMsg); }
      });

      var icsHelpBody = el('div', { class: 'provider-note', hidden: true }, [
        el('p', { text: t('parent.ics_help_intro') }),
        el('ul', {}, [
          el('li', { text: t('parent.ics_help_google') }),
          el('li', { text: t('parent.ics_help_outlook') }),
          el('li', { text: t('parent.ics_help_apple') })
        ])
      ]);
      var icsHelpToggle = el('button', {
        class: 'btn btn--quiet', type: 'button', text: t('parent.ics_help_toggle'),
        onclick: function () { icsHelpBody.hidden = !icsHelpBody.hidden; }
      });

      var connectGoogleBtn = el('a', {
        class: 'btn btn--quiet', href: '/calendar-sync/google/connect?org_id=' + org.id,
        text: t('parent.connect_google')
      });

      var syncBtn = el('button', {
        class: 'btn btn--primary', type: 'button', text: t('parent.sync_now'),
        onclick: function () { parent.syncOrg(org.id, statusMsg); }
      });

      var card = el('article', { class: 'provider-card' }, [
        el('h3', { class: 'provider-card__name', text: org.name }),
        el('p', { class: 'direction-tag direction-tag--pull', text: t('parent.direction_pull_tag') }),
        el('p', { class: 'field-label', text: statusText }),
        el('div', { class: 'actions' }, [icsInput, connectIcsBtn, icsHelpToggle]),
        icsHelpBody,
        el('div', { class: 'actions' }, [connectGoogleBtn, syncBtn]),
        statusMsg
      ]);

      if (org.id === chooseOrgId) {
        var pickerHost = el('div', { class: 'calendar-picker' });
        card.insertBefore(pickerHost, statusMsg);
        parent.loadCalendarPicker({ kind: 'org', id: org.id, name: org.name }, pickerHost, statusMsg);
      }

      return card;
    },

    loadKidCalendars: function () {
      var host = document.getElementById('parent-kid-calendars');
      if (!host) return;
      var chooseKidId = Number(new URLSearchParams(global.location.search).get('choose_kid_calendar'));
      api('/calendar-sync/google/kid/list').then(function (kids) {
        parent.renderKidCalendars(host, kids, chooseKidId);
      }).catch(function () { failed(host); });
    },

    renderKidCalendars: function (host, kids, chooseKidId) {
      clear(host);
      if (!kids.length) {
        host.appendChild(el('p', { class: 'empty', text: t('parent.no_kids_yet') }));
      } else {
        kids.forEach(function (kidRow) { host.appendChild(parent.kidCalendarCard(kidRow, chooseKidId)); });
      }
      host.appendChild(parent.addKidForm());
    },

    // Families with more than one kid on Mew usually add the second one
    // well after their own first setup - this is the only place to do that.
    addKidForm: function () {
      var nameInput = el('input', { type: 'text', placeholder: t('parent.add_kid_name_placeholder') });
      var statusMsg = el('p', { class: 'log-row__meta' });
      var addBtn = el('button', {
        class: 'btn btn--primary', type: 'button', text: t('parent.add_kid'),
        onclick: function () {
          var name = (nameInput.value || '').trim();
          if (!name) return;
          statusMsg.textContent = t('ui.loading');
          api('/onboarding/kids', { method: 'POST', body: { display_name: name } })
            .then(function () {
              nameInput.value = '';
              parent.loadKidCalendars();
            })
            .catch(function () { statusMsg.textContent = t('ui.error'); });
        }
      });
      return el('article', { class: 'provider-card' }, [
        el('p', { class: 'field-label', text: t('parent.add_kid_heading') }),
        el('div', { class: 'actions' }, [nameInput, addBtn]),
        statusMsg
      ]);
    },

    kidCalendarCard: function (kidRow, chooseKidId) {
      var statusMsg = el('p', { class: 'log-row__meta' });
      var statusText = kidRow.calendar_connected
        ? (kidRow.calendar_display_name
          ? t('parent.kid_calendar_connected_named', { name: kidRow.calendar_display_name })
          : t('parent.kid_calendar_connected'))
        : t('parent.kid_calendar_not_connected');

      var connectGoogleBtn = el('a', {
        class: 'btn btn--quiet', href: '/calendar-sync/google/kid/connect?child_id=' + kidRow.id,
        text: t('parent.connect_kid_google')
      });

      var card = el('article', { class: 'provider-card' }, [
        el('h3', { class: 'provider-card__name', text: kidRow.name }),
        el('p', { class: 'direction-tag direction-tag--push', text: t('parent.direction_push_tag') }),
        el('p', { class: 'field-label', text: statusText }),
        el('div', { class: 'actions' }, [connectGoogleBtn]),
        statusMsg
      ]);

      if (kidRow.id === chooseKidId) {
        var pickerHost = el('div', { class: 'calendar-picker' });
        card.insertBefore(pickerHost, statusMsg);
        parent.loadCalendarPicker({ kind: 'kid', id: kidRow.id, name: kidRow.name }, pickerHost, statusMsg);
      }

      return card;
    },

    // target is { kind: 'org'|'kid', id, name }: which picker/save endpoint
    // to use, and whose name to put in the direction hint below. A
    // provider's calendar is a read source (pull), a kid's is a push
    // target - same chip-list UI either way, which is exactly why the
    // hint matters: nothing else on this screen says which one you're in.
    loadCalendarPicker: function (target, host, statusMsg) {
      host.textContent = t('ui.loading');
      var url = target.kind === 'kid'
        ? '/calendar-sync/google/kid/calendars?child_id=' + target.id
        : '/calendar-sync/google/calendars?org_id=' + target.id;
      api(url).then(function (data) {
        parent.renderCalendarPicker(target, host, data.calendars || [], statusMsg);
      }).catch(function () { host.textContent = t('ui.error'); });
    },

    renderCalendarPicker: function (target, host, calendars, statusMsg) {
      clear(host);
      if (!calendars.length) {
        host.appendChild(el('p', { class: 'empty', text: t('parent.no_calendars_found') }));
        return;
      }
      var hintKey = target.kind === 'kid' ? 'parent.picker_hint_push' : 'parent.picker_hint_pull';
      host.appendChild(el('p', { class: 'calendar-picker__hint', text: t(hintKey, { name: target.name }) }));
      host.appendChild(el('p', { class: 'field-label', text: t('parent.choose_calendar') }));
      var chips = calendars.map(function (cal) {
        var label = cal.primary
          ? t('parent.calendar_primary_label', { name: cal.summary })
          : cal.summary;
        return el('button', {
          class: 'chip', type: 'button', text: label,
          onclick: function () { parent.chooseGoogleCalendar(target, cal.id, cal.summary, host, statusMsg); }
        });
      });
      host.appendChild(el('div', { class: 'chips' }, chips));
    },

    chooseGoogleCalendar: function (target, calendarId, calendarName, pickerHost, statusMsg) {
      statusMsg.textContent = t('ui.loading');
      var url = target.kind === 'kid'
        ? '/calendar-sync/kids/' + target.id + '/calendar'
        : '/calendar-sync/orgs/' + target.id + '/calendar';
      var queryParam = target.kind === 'kid' ? 'choose_kid_calendar' : 'choose_calendar_org';
      api(url, {
        method: 'PUT',
        body: { calendar_provider: 'google', calendar_account_id: calendarId, calendar_display_name: calendarName }
      }).then(function (report) {
        if (target.kind === 'kid') {
          statusMsg.textContent = t('parent.kid_calendar_connect_ok');
        } else {
          parent.showSyncReport(statusMsg, report);
        }
        clear(pickerHost);
        var url2 = new URL(global.location.href);
        url2.searchParams.delete(queryParam);
        global.history.replaceState(null, '', url2.toString());
      }).catch(function (err) {
        statusMsg.textContent = (err && err.detail) || t('ui.error');
      });
    },

    connectIcs: function (orgId, url, statusMsg) {
      var trimmed = (url || '').trim();
      if (!trimmed) return;
      api('/calendar-sync/orgs/' + orgId + '/calendar', {
        method: 'PUT', body: { calendar_provider: 'ics', calendar_account_id: trimmed }
      }).then(function (report) { parent.showSyncReport(statusMsg, report); })
        .catch(function () { statusMsg.textContent = t('ui.error'); });
    },

    syncOrg: function (orgId, statusMsg) {
      statusMsg.textContent = t('ui.loading');
      api('/calendar-sync/pull?provider_org_id=' + orgId, { method: 'POST' }).then(function (reports) {
        var report = reports[0];
        if (!report) { statusMsg.textContent = t('parent.calendar_not_connected'); return; }
        parent.showSyncReport(statusMsg, report);
      }).catch(function () { statusMsg.textContent = t('ui.error'); });
    },

    showSyncReport: function (statusMsg, report) {
      statusMsg.textContent = report.ok
        ? t('parent.sync_ok', { count: report.created + report.updated })
        : t('parent.sync_failed', { error: report.error });
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

  // ------------------------------------------------------------- setup

  var setup = {
    state: { child: null },

    start: function () {
      document.getElementById('wizard-child-continue').addEventListener('click', setup.continueToProvider);
      document.getElementById('wizard-finish').addEventListener('click', function () { setup.submit(false); });
      document.getElementById('wizard-skip').addEventListener('click', function () { setup.submit(true); });
    },

    continueToProvider: function () {
      var name = document.getElementById('wizard-child-name').value.trim();
      var errorNode = document.getElementById('wizard-child-error');
      if (!name) {
        errorNode.textContent = t('wizard.name_required');
        errorNode.hidden = false;
        return;
      }
      errorNode.hidden = true;

      var ageValue = document.getElementById('wizard-child-age').value;
      setup.state.child = { display_name: name };
      if (ageValue !== '') setup.state.child.age = Number(ageValue);

      document.getElementById('wizard-child').hidden = true;
      document.getElementById('wizard-provider').hidden = false;
      document.getElementById('wizard-provider-name').focus();
    },

    /** Skipping and finishing both save the child; only the provider list differs. */
    submit: function (skipProvider) {
      var payload = { child: setup.state.child, providers: [] };

      if (!skipProvider) {
        var providerName = document.getElementById('wizard-provider-name').value.trim();
        if (providerName) {
          payload.providers.push({
            name: providerName,
            kind: document.getElementById('wizard-provider-kind').value
          });
        }
      }

      var errorNode = document.getElementById('wizard-provider-error');
      errorNode.hidden = true;

      api('/onboarding/setup', { method: 'POST', body: payload }).then(function (result) {
        global.location.href = result.caregiver_screen || '/app/parent';
      }).catch(function () {
        errorNode.textContent = t('ui.error');
        errorNode.hidden = false;
      });
    }
  };

  global.Mew = { t: t, api: api, parent: parent, kid: kid, provider: provider, setup: setup, announce: announce };
})(window);
