/* ============================================================
   AVISHKA PATHOLOGY — Multi-Step Booking Form
   5 Steps: Details → Symptoms → Tests → Slot → Confirm
   ============================================================ */

// ── State ────────────────────────────────────────────────────
const bookingState = {
  selectedSymptoms: [],
  selectedTests:    new Set(),
  selectedSlot:     null,
  slots:            [],
};

// ── Step Navigation ──────────────────────────────────────────
function bookingStep(step) {
  // Validate before advancing
  if (step > 1 && !validateStep(step - 1)) return;

  for (let i = 1; i <= 5; i++) {
    const panel = document.getElementById('bpanel-' + i);
    const ind   = document.getElementById('step-ind-' + i);
    if (!panel || !ind) continue;

    panel.classList.toggle('active', i === step);
    ind.classList.remove('active', 'done');
    if (i < step)  ind.classList.add('done');
    if (i === step) ind.classList.add('active');
  }

  // Load dynamic content per step
  if (step === 3) renderTestSelectGrid();
  if (step === 4) { renderSlots(); renderSummaryPreview(); }

  window.scrollTo({ top: document.getElementById('page-booking').offsetTop - 80, behavior: 'smooth' });
}

function validateStep(step) {
  if (step === 1) {
    const name  = document.getElementById('bName')?.value.trim();
    const phone = document.getElementById('bPhone')?.value.trim();
    if (!name)  { alert('Please enter the patient name.'); return false; }
    if (!phone || phone.replace(/\D/g,'').length < 10) {
      alert('Please enter a valid 10-digit phone number.'); return false;
    }
  }
  if (step === 3) {
    if (bookingState.selectedTests.size === 0) {
      alert('Please select at least one test.'); return false;
    }
  }
  if (step === 4) {
    if (!bookingState.selectedSlot) {
      alert('Please select an appointment slot.'); return false;
    }
  }
  return true;
}

// ── Symptom Selection ────────────────────────────────────────
const SYMPTOM_MAP = {
  'fatigue':       ['CBC','THYROID','VITB12','VITD'],
  'fever':         ['CBC','URINE'],
  'diabetes':      ['BSF','BSPP','HBA1C'],
  'thyroid':       ['THYROID'],
  'chest pain':    ['ECG','LIPID'],
  'cholesterol':   ['LIPID'],
  'kidney':        ['KFT','URINE'],
  'liver':         ['LFT'],
  'weight gain':   ['THYROID','BSF','LIPID'],
  'hair fall':     ['THYROID','VITB12','VITD','CBC'],
  'anemia':        ['CBC','VITB12'],
  'bone pain':     ['VITD','CBC'],
  'routine checkup':['CBC','BSF','LIPID','KFT','LFT','URINE'],
  'full body':     ['CBC','BSF','LIPID','KFT','LFT','THYROID','VITD','VITB12','URINE'],
};

function toggleSymptom(el, key) {
  el.classList.toggle('selected');
  const idx = bookingState.selectedSymptoms.indexOf(key);
  if (idx === -1) bookingState.selectedSymptoms.push(key);
  else            bookingState.selectedSymptoms.splice(idx, 1);
}

function getRecommendedTests() {
  const extra = document.getElementById('bSymptomText')?.value.toLowerCase() || '';
  const codes = new Set();

  bookingState.selectedSymptoms.forEach(s => {
    (SYMPTOM_MAP[s] || []).forEach(c => codes.add(c));
  });

  // Parse extra text
  Object.entries(SYMPTOM_MAP).forEach(([kw, cs]) => {
    if (extra.includes(kw)) cs.forEach(c => codes.add(c));
  });

  return codes;
}

// ── Test Selection Grid ──────────────────────────────────────
function renderTestSelectGrid() {
  const grid = document.getElementById('testSelectGrid');
  if (!grid) return;

  // Pre-select recommended tests
  const recommended = getRecommendedTests();
  if (recommended.size > 0) bookingState.selectedTests = new Set(recommended);

  grid.innerHTML = Object.entries(TEST_CATALOG).map(([code, test]) => {
    const sel = bookingState.selectedTests.has(code);
    return `
      <div class="test-select-card ${sel ? 'selected' : ''}" id="tsc-${code}" onclick="toggleTest('${code}')">
        <div class="tsc-top">
          <div style="display:flex;align-items:center;gap:8px;">
            <span>${test.icon}</span>
            <span class="tsc-name">${test.name}</span>
          </div>
          <div class="tsc-check">${sel ? '✓' : ''}</div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
          <div class="tsc-prep">🍽 ${test.prep}</div>
          <div class="tsc-price">₹${test.price}</div>
        </div>
      </div>`;
  }).join('');

  updateTotal();
}

function toggleTest(code) {
  const card = document.getElementById('tsc-' + code);
  if (!card) return;
  const sel = card.classList.toggle('selected');
  if (sel) {
    bookingState.selectedTests.add(code);
    card.querySelector('.tsc-check').textContent = '✓';
  } else {
    bookingState.selectedTests.delete(code);
    card.querySelector('.tsc-check').textContent = '';
  }
  updateTotal();
}

function updateTotal() {
  let total = 0;
  bookingState.selectedTests.forEach(code => {
    if (TEST_CATALOG[code]) total += TEST_CATALOG[code].price;
  });
  const el = document.getElementById('selTotal');
  if (el) el.textContent = '₹' + total.toLocaleString();
}

// Pre-select a test from chatbot
function preSelectTest(code) {
  bookingState.selectedTests.add(code);
  bookingStep(3);
}

// ── Slot Rendering ───────────────────────────────────────────
async function renderSlots() {
  const grid = document.getElementById('slotsGrid');
  if (!grid) return;

  // Use locally generated slots (no API call needed)
  const slots = generateSlots();
  bookingState.slots = slots;

  grid.innerHTML = slots.map((s, i) => `
    <div class="slot-card" id="slot-${i}" onclick="selectSlot(${i})">
      <div class="slot-day">${s.day}</div>
      <div class="slot-date">${s.dateDisplay}</div>
      <div class="slot-time">${s.time}</div>
    </div>`).join('');
}

function generateSlots() {
  const slots = [];
  const times = ['07:00 AM','08:30 AM','10:00 AM','11:30 AM','05:00 PM','06:30 PM'];
  const today = new Date();

  for (let i = 1; i <= 6; i++) {
    const d = new Date(today); d.setDate(today.getDate() + i);
    const day = d.getDay();
    const available = day === 0 ? times.slice(0,2) : times;
    const time = available[Math.floor(Math.random() * available.length)];

    slots.push({
      date:        d.toISOString().slice(0,10),
      day:         d.toLocaleDateString('en-IN', { weekday: 'long' }),
      dateDisplay: d.toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }),
      time,
    });
  }
  return slots;
}

function selectSlot(i) {
  document.querySelectorAll('.slot-card').forEach((c, idx) =>
    c.classList.toggle('selected', idx === i));
  bookingState.selectedSlot = bookingState.slots[i];
  renderSummaryPreview();
}

function renderSummaryPreview() {
  const summary = document.getElementById('bookingSummary');
  if (!summary) return;

  const name  = document.getElementById('bName')?.value || '—';
  const phone = document.getElementById('bPhone')?.value || '—';
  const tests = Array.from(bookingState.selectedTests).map(c => TEST_CATALOG[c]?.name).join(', ') || '—';
  const slot  = bookingState.selectedSlot
    ? `${bookingState.selectedSlot.day}, ${bookingState.selectedSlot.dateDisplay} at ${bookingState.selectedSlot.time}`
    : 'Not selected';

  let total = 0;
  bookingState.selectedTests.forEach(c => { if (TEST_CATALOG[c]) total += TEST_CATALOG[c].price; });

  document.getElementById('sumName').textContent  = name;
  document.getElementById('sumPhone').textContent = phone;
  document.getElementById('sumTests').textContent = tests;
  document.getElementById('sumSlot').textContent  = slot;
  document.getElementById('sumTotal').textContent = '₹' + total.toLocaleString();

  summary.style.display = bookingState.selectedSlot ? 'block' : 'none';
}

// ── Submit Booking ───────────────────────────────────────────
async function submitBooking() {
  if (!validateStep(4)) return;

  const btn = document.getElementById('bookingSubmitBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Submitting...';

  const payload = {
    patient_name:     document.getElementById('bName').value.trim(),
    age:              parseInt(document.getElementById('bAge')?.value) || null,
    gender:           document.getElementById('bGender')?.value || null,
    phone:            document.getElementById('bPhone').value.trim(),
    email:            document.getElementById('bEmail')?.value.trim() || null,
    symptoms:         bookingState.selectedSymptoms.join(', ') || null,
    test_codes:       Array.from(bookingState.selectedTests),
    appointment_date: bookingState.selectedSlot.date,
    appointment_slot: bookingState.selectedSlot.time,
    notes:            document.getElementById('bNotes')?.value.trim() || null,
  };

  try {
    const res  = await fetch('/api/booking/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Booking failed');

    // Show confirmation
    document.getElementById('confirmedRef').textContent = data.reference;
    document.getElementById('confirmedMsg').textContent = data.message;

    // Set pay amount for the proof card
    const amt = document.getElementById('payAmountDisplay');
    if (amt) amt.textContent = '₹' + data.total_cost.toLocaleString();

    bookingStep(5);
    resetBookingState();
  } catch (err) {
    alert('Booking failed: ' + err.message + '\nPlease call 7355230710 directly.');
    btn.disabled = false;
    btn.textContent = '✅ Confirm Appointment';
  }
}

function resetBookingState() {
  bookingState.selectedSymptoms = [];
  bookingState.selectedTests    = new Set();
  bookingState.selectedSlot     = null;
  // Reset form fields
  ['bName','bAge','bPhone','bEmail','bSymptomText','bNotes'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('bGender').value = '';
  document.querySelectorAll('.symptom-chip').forEach(c => c.classList.remove('selected'));
}

// ── Contact Form ─────────────────────────────────────────────
async function submitContact(e) {
  e.preventDefault();
  const btn = document.getElementById('contactSubmitBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Sending...';

  const payload = {
    name:    document.getElementById('cName').value.trim(),
    email:   document.getElementById('cEmail').value.trim(),
    phone:   document.getElementById('cPhone')?.value.trim() || null,
    subject: document.getElementById('cSubject').value,
    message: document.getElementById('cMessage').value.trim(),
  };

  try {
    const res  = await fetch('/api/contact/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    document.getElementById('contactSuccess').textContent = '✅ ' + data.message;
    document.getElementById('contactSuccess').classList.add('show');
    document.getElementById('contactForm').reset();
  } catch {
    alert('Could not send message. Please email avishka.pathology@outlook.com directly.');
  } finally {
    btn.disabled = false;
    btn.textContent = '📤 Send Message';
  }
}

// ── Init Booking Page ────────────────────────────────────────
function initBookingPage() {
  // Reset to step 1 each time the page is opened fresh
  for (let i = 1; i <= 5; i++) {
    const p = document.getElementById('bpanel-' + i);
    const s = document.getElementById('step-ind-' + i);
    if (p) p.classList.toggle('active', i === 1);
    if (s) { s.classList.remove('active','done'); if (i === 1) s.classList.add('active'); }
  }
}

// ── UPI Copy ─────────────────────────────────────────────────
function copyUPI() {
  const upi = document.getElementById('upiIdText')?.textContent || '7355230710@upi';
  navigator.clipboard.writeText(upi).then(() => {
    const btn = event.target;
    btn.textContent = 'Copied!';
    btn.style.color = '#22c55e';
    setTimeout(() => { btn.textContent = 'Copy'; btn.style.color = ''; }, 2000);
  }).catch(() => {
    prompt('Copy this UPI ID:', upi);
  });
}

// Expose globally
window.copyUPI         = copyUPI;
window.bookingStep     = bookingStep;
window.toggleSymptom = toggleSymptom;
window.toggleTest   = toggleTest;
window.selectSlot   = selectSlot;
window.submitBooking = submitBooking;
window.submitContact = submitContact;
window.preSelectTest = preSelectTest;
window.initBookingPage = initBookingPage;
window.filterTests  = filterTests;
