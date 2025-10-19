document.addEventListener('DOMContentLoaded', () => {
  const subcategoryDropdown = document.getElementById('subcategory-dropdown');
  const statusFilter = document.getElementById('status-filter');
  const competitionDetails = document.getElementById('competition-details');
  const categoryTitle = document.getElementById('category-title');

  const urlParams = new URLSearchParams(window.location.search);
  const category = urlParams.get('category');
  const isAdmin = false; // Users can't access admin controls

  let allCompetitions = {};
  let currentCategoryData = {};

  function loadData() {
    getData()
      .then(data => {
        allCompetitions = data;
        if (category && data[category]) {
          categoryTitle.textContent = `Category: ${formatName(category)}`;
          currentCategoryData = data[category];
          populateSubcategoryDropdown(currentCategoryData);
          render();
        } else {
          competitionDetails.innerHTML = `<div class="error-message">Invalid category</div>`;
        }
      })
      .catch(err => {
        console.error('Error loading competitions data', err);
        competitionDetails.innerHTML = `<div class="error-message">Error loading data</div>`;
      });
  }

  loadData();

  function getData() {
    return fetch('/api/competitions', { cache: 'no-store' })
      .then(r => {
        if (!r.ok) throw new Error('Failed to fetch competitions');
        return r.json();
      })
      .catch(err => {
        console.error('Error loading competitions data', err);
        competitionDetails.innerHTML = `<div class="error-message">Error loading data</div>`;
        return {};
      });
  }

  function populateSubcategoryDropdown(categoryData) {
    subcategoryDropdown.innerHTML = `<option value="">-- Select a Subcategory --</option>`;
    Object.keys(categoryData).sort().forEach(sub => {
      let option = document.createElement('option');
      option.value = sub;
      option.textContent = formatName(sub);
      subcategoryDropdown.appendChild(option);
    });

    subcategoryDropdown.addEventListener('change', render);
    statusFilter.addEventListener('change', render);
  }

  function render() {
    const subName = subcategoryDropdown.value;
    if (!subName) {
      competitionDetails.innerHTML = `<div class="select-prompt">Please select a subcategory.</div>`;
      return;
    }
    const comps = currentCategoryData[subName] || [];
    const filtered = comps.filter(c => statusFor(c) === statusFilterValue() || statusFilterValue() === 'all');
    displaySubcategoryCompetitions(filtered, subName);
  }

  function statusFilterValue() {
    return statusFilter.value;
  }

  function statusFor(comp) {
    const d = tryParseDate(comp.date);
    if (!d) {
      return 'upcoming';
    }
    const now = new Date();
    return d >= now ? 'scheduled' : 'past';
  }

  function tryParseDate(str) {
    if (!str) return null;
    const normalized = ('' + str).trim().toLowerCase();
    if (['tba', 'coming soon', 'coming soon!'].includes(normalized)) return null;
    if (normalized.includes('valentine')) return new Date('2026-02-14');
    const d = new Date(str);
    return isNaN(d.getTime()) ? null : d;
  }

  function displaySubcategoryCompetitions(competitions, subName) {
    if (!competitions || !competitions.length) {
      competitionDetails.innerHTML = `<div class="no-competitions">No competitions in "${formatName(subName)}" for this filter.</div>`;
      return;
    }
    competitionDetails.innerHTML = competitions.map(comp => {
      const s = statusFor(comp);
      const badgeLabel = s === 'scheduled' ? 'Scheduled' : (s === 'past' ? 'Past' : 'Upcoming / TBA');
      const d = tryParseDate(comp.date);
      const dateText = d ? d.toDateString() : comp.date;
      const encodedName = encodeURIComponent(comp.name);
      let actions = `
        ${comp.link && comp.link !== '#' ? `<a href="${comp.link}" class="register-btn" target="_blank" rel="noopener">Register</a>` : `<a href="https://docs.google.com/forms/d/e/1FAIpQLSfRCqSX2PG-4lDZMvLETC0Onx5S7dodaVnm6mPVcPgJq7GrYg/viewform" class="register-btn" target="_blank" rel="noopener">Register</a>`}
        <a href="https://wa.me/916366533719?text=I%20want%20to%20join%20${encodedName}" target="_blank" class="whatsapp-btn" rel="noopener">Join via WhatsApp</a>
      `;
      return `
      <div class="competition-card">
        <img class="competition-image" src="${comp.image || 'https://via.placeholder.com/250?text=No+Image'}" alt="${comp.name}">
        <div class="competition-content">
          <h3>${comp.name}</h3>
          <div class="comp-badges">
            <span class="comp-badge">${badgeLabel}</span>
          </div>
          <p class="competition-description">${comp.description}</p>
          <div class="competition-meta">
            <p><strong>Date:</strong> ${dateText}</p>
            ${comp.location ? `<p><strong>Location:</strong> ${comp.location}</p>` : ''}
            ${comp.participant_limit ? `<p><strong>Participant Limit:</strong> ${comp.participant_limit}</p>` : ''}
            ${comp.entry_fee ? `<p><strong>Entry Fee:</strong> ₹${comp.entry_fee}</p>` : ''}
            ${comp.prizes ? `<p><strong>Prizes:</strong> ${comp.prizes}</p>` : ''}
          </div>
          <div class="competition-actions">
            ${actions}
          </div>
        </div>
      </div>`;
    }).join('');
  }

  function formatName(str) { return str.charAt(0).toUpperCase() + str.slice(1); }
});

