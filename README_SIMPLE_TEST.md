# Debug Test - Token is Saved, Now Test API Call

Good news! Token is being saved to localStorage.

## Next Step: Test the API call directly

After signing in, open Console (F12) and run this:

```javascript
const token = localStorage.getItem('mew_token');
console.log('Testing API with token:', token.substring(0, 20) + '...');

fetch('https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=5', {
    headers: { 'Authorization': 'Bearer ' + token }
})
.then(response => {
    console.log('Status:', response.status);
    return response.json();
})
.then(data => {
    console.log('Response:', data);
})
.catch(error => {
    console.error('Error:', error);
});
```

## What to Tell Me:

1. **Status:** What number? (200, 401, 400, 500?)
2. **Response:** Copy the entire JSON that prints
3. **Error:** If there's an error, what does it say?

This will tell us exactly what the API is returning!
