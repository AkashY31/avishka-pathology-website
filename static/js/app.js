/* ============================================================
   AVISHKA PATHOLOGY — Main App JS
   SPA Router, Theme Toggle, Scroll Reveal, Counters
   ============================================================ */

// ── Theme ────────────────────────────────────────────────────
const html = document.documentElement;
const themeBtn = document.getElementById('themeBtn');

function applyTheme(t) {
  html.setAttribute('data-theme', t);
  themeBtn.textContent = t === 'dark' ? '☀️' : '🌙';
  localStorage.setItem('avishka-theme', t);
}

function toggleTheme() {
  applyTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}

// Apply saved theme on load
applyTheme(localStorage.getItem('avishka-theme') || 'light');

// ── SPA Router ───────────────────────────────────────────────
const pages   = ['home', 'services', 'about', 'contact', 'booking'];
const navLinks = document.querySelectorAll('.nav-links a, .footer-col a, .mobile-menu a');

function showPage(name) {
  pages.forEach(p => {
    const el = document.getElementById('page-' + p);
    if (el) el.classList.toggle('active', p === name);
  });

  // Update nav active state
  document.querySelectorAll('.nav-links a').forEach(a => {
    a.classList.toggle('active', a.textContent.trim().toLowerCase().includes(name));
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger page-specific logic
  if (name === 'services') renderServicesPage();
  if (name === 'booking')  initBookingPage();

  // Re-trigger scroll reveals for the new page
  setTimeout(checkReveal, 100);
}

// ── Navbar Scroll Effect ─────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 20);
});

// ── Mobile Menu ──────────────────────────────────────────────
function toggleMobileMenu() {
  document.getElementById('mobileMenu').classList.toggle('open');
}

// ── Scroll Reveal ────────────────────────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.12 });

function checkReveal() {
  document.querySelectorAll('.reveal:not(.visible)').forEach(el => revealObserver.observe(el));
}
checkReveal();

// ── Animated Counters ────────────────────────────────────────
function animateCounter(id, target, duration = 1600) {
  const el = document.getElementById(id);
  if (!el) return;
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = Math.round(start).toLocaleString();
    if (start >= target) clearInterval(timer);
  }, 16);
}

// Trigger counters when hero is visible
const heroObs = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) {
    animateCounter('cnt1', 2000);
    animateCounter('cnt2', 13, 800);
    animateCounter('cnt3', 2, 800);
    heroObs.disconnect();
  }
}, { threshold: 0.3 });

const heroEl = document.querySelector('.hero');
if (heroEl) heroObs.observe(heroEl);

// ── Test Catalog (inline — no extra fetch needed) ────────────
const TEST_CATALOG = {
  CBC:      { name: 'Complete Blood Count',        price: 300,  category: 'Blood',         prep: 'No fasting required',          desc: 'Detects infections, anemia, blood disorders.',   icon: '🩸', duration: 'Same Day' },
  BSF:      { name: 'Blood Sugar Fasting',         price: 120,  category: 'Diabetes',      prep: '8–12 hours fasting',           desc: 'Measures glucose after fasting. Diabetes test.',  icon: '💉', duration: 'Same Day' },
  BSPP:     { name: 'Blood Sugar Post Prandial',   price: 120,  category: 'Diabetes',      prep: '2 hours after meal',           desc: 'Glucose 2 hrs post-meal. Monitors diabetes.',    icon: '💉', duration: 'Same Day' },
  BSRANDOM: { name: 'Blood Sugar Random',          price: 120,  category: 'Diabetes',      prep: 'No fasting required',          desc: 'Quick blood glucose check anytime.',             icon: '💉', duration: 'Same Day' },
  LIPID:    { name: 'Lipid Profile',               price: 350,  category: 'Heart Health',  prep: '12 hours fasting',             desc: 'Cholesterol, LDL, HDL, triglycerides.',          icon: '❤️', duration: 'Same Day' },
  THYROID:  { name: 'Thyroid Profile (T3,T4,TSH)', price: 600,  category: 'Thyroid',       prep: 'No fasting required',          desc: 'Evaluates thyroid gland function.',              icon: '🦋', duration: 'Same Day' },
  LFT:      { name: 'Liver Function Test',         price: 400,  category: 'Organ Function',prep: '12 hours fasting',             desc: 'Assesses liver health — enzymes & bilirubin.',   icon: '🏥', duration: 'Same Day' },
  KFT:      { name: 'Kidney Function Test',        price: 350,  category: 'Organ Function',prep: 'No fasting required',          desc: 'Creatinine, urea — evaluates kidney health.',    icon: '🏥', duration: 'Same Day' },
  URINE:    { name: 'Urine Routine & Microscopy',  price: 100,  category: 'Urine',         prep: 'Early morning sample',         desc: 'Detects infections, kidney & diabetes markers.', icon: '🔬', duration: 'Same Day' },
  VITD:     { name: 'Vitamin D (25-OH)',            price: 800,  category: 'Vitamins',      prep: 'No fasting required',          desc: 'Bone health, immunity, mood regulator.',         icon: '☀️', duration: '1–2 Days' },
  VITB12:   { name: 'Vitamin B12',                 price: 600,  category: 'Vitamins',      prep: 'No fasting required',          desc: 'Nerve function & red blood cell health.',        icon: '🧬', duration: '1–2 Days' },
  HBA1C:    { name: 'HbA1c (Glycated Hemoglobin)', price: 350,  category: 'Diabetes',      prep: 'No fasting required',          desc: '3-month avg blood sugar. Diabetes monitoring.',  icon: '📊', duration: 'Same Day' },
  ECG:      { name: 'ECG / Electrocardiogram',     price: 200,  category: 'Heart Health',  prep: 'Loose, comfortable clothing',  desc: 'Heart electrical activity. Arrhythmia detection.', icon: '💓', duration: 'Immediate' },
};

// ── Render Test Cards ────────────────────────────────────────
function makeTestCard(code, test, clickable = false) {
  return `
    <div class="test-card" ${clickable ? `onclick="showPage('booking')"` : ''}>
      <div class="test-card-top">
        <div class="test-icon">${test.icon}</div>
        <div class="test-price">₹${test.price}<span>/test</span></div>
      </div>
      <div class="test-name">${test.name}</div>
      <div class="test-desc">${test.desc}</div>
      <div class="test-meta">
        <span class="test-tag">📁 ${test.category}</span>
        <span class="test-tag">⏱ ${test.duration}</span>
        <span class="test-tag">🍽 ${test.prep.length > 20 ? test.prep.slice(0,20)+'…' : test.prep}</span>
      </div>
    </div>`;
}

// Home page — show first 6 tests
function renderHomePage() {
  const grid = document.getElementById('home-tests-grid');
  if (!grid) return;
  const codes = Object.keys(TEST_CATALOG).slice(0, 6);
  grid.innerHTML = codes.map(c => makeTestCard(c, TEST_CATALOG[c], true)).join('');
  checkReveal();
}

// ── Services Page ────────────────────────────────────────────
let currentCategory = 'all';

function renderServicesPage() {
  filterTests(currentCategory);
}

function filterTests(category, btn) {
  currentCategory = category;

  // Update buttons
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const grid = document.getElementById('services-tests-grid');
  if (!grid) return;

  const entries = Object.entries(TEST_CATALOG).filter(([, t]) =>
    category === 'all' || t.category === category
  );

  grid.innerHTML = entries.map(([code, test]) => makeTestCard(code, test, true)).join('');
}

// ── Init ─────────────────────────────────────────────────────
renderHomePage();
