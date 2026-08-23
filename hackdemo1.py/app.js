const samples = {
  scam: {
    text: `Dear Candidate, CONGRATULATIONS!!! You have been selected for a work from home opportunity with Google. Earn ₹5000/day with no experience needed. Limited seats, apply immediately within 2 hours. To confirm your offer, pay a refundable registration fee of ₹999 and send your Aadhaar and OTP. Click here: https://bit.ly/google-careers-apply`,
    sender_email: 'googlecareers.hr@gmail.com', claimed_company: 'Google', url: ''
  },
  safe: {
    text: `Hello Priya, thank you for applying for the Product Design Intern role at Northstar Labs. We would like to invite you to a 30-minute video interview on Tuesday, 27 August at 3 PM. This internship is paid ₹20,000 per month. You can review the role and interview details on our official careers page: https://northstarlabs.com/careers/product-design-intern. Please reply if the time works for you.`,
    sender_email: 'maya@northstarlabs.com', claimed_company: 'Northstar Labs', url: 'https://northstarlabs.com/careers/product-design-intern'
  }
};
const $ = id => document.getElementById(id);
$('message').addEventListener('input', () => $('char-count').textContent = `${$('message').value.length} characters`);
document.querySelectorAll('.sample-btn').forEach(button => button.addEventListener('click', () => {
  const sample = samples[button.dataset.sample]; $('message').value = sample.text; $('sender').value = sample.sender_email; $('company').value = sample.claimed_company; $('url').value = sample.url; $('message').dispatchEvent(new Event('input')); analyze();
}));
async function analyze() {
  const button = $('analyze'); button.disabled = true; button.querySelector('span').textContent = 'Analyzing...';
  try {
    const response = await fetch('/api/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:$('message').value, sender_email:$('sender').value, claimed_company:$('company').value, url:$('url').value})});
    const result = await response.json(); render(result);
  } catch (error) { alert('Could not reach the local analyzer. Is the Python server running?'); }
  button.disabled = false; button.querySelector('span').textContent = 'Analyze opportunity';
}
function render(result) {
  $('empty-state').classList.add('hidden'); $('results').classList.remove('hidden');
  $('score').textContent = result.score; $('score').style.color = result.color; $('risk-label').textContent = result.label; $('risk-label').style.color = result.color; $('summary').textContent = result.summary; $('meter-fill').style.width = `${result.score}%`; $('meter-fill').style.background = result.color; $('finding-count').textContent = `${result.findings.length} signal${result.findings.length === 1 ? '' : 's'}`;
  $('findings').innerHTML = result.findings.length ? result.findings.map(item => `<article class="finding"><div class="finding-top"><span class="finding-icon">&#9679;</span><div><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.description)}</p></div></div>${item.evidence.map(e => `<div class="evidence">“${escapeHtml(e)}”</div>`).join('')}</article>`).join('') : '<p class="finding"><strong>No automated red flags found.</strong><br><span style="color:#65717d;font-size:12px">Still verify the sender and opportunity through an independent official channel.</span></p>';
  const best = result.findings[0]?.advice || 'Verify the role through the company’s official careers page before replying.'; $('advice').textContent = best;
}
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[character])); }
$('analyze').addEventListener('click', analyze);
$('reset').addEventListener('click', () => { $('results').classList.add('hidden'); $('empty-state').classList.remove('hidden'); $('message').focus(); });
