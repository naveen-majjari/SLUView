// SLUview: dynamic review loader for Column C
// Expected data format: { "reviews": [ { name, rating, date, text, business, city, price } ] }
(function(){
  const root = document.getElementById('reviews');
  if(!root){
    console.warn('No #reviews container found.');
    return;
  }

  function createReviewCard(r){
    const el = document.createElement('article');
    el.className = 'review';
    const stars = (()=>{
      const n = Math.max(0, Math.min(5, Math.round(Number(r.rating)||0)));
      return '★'.repeat(n) + (n ? '' : '');
    })();
    el.innerHTML = `
      <div class="head">
        <div class="name">${escapeHtml(r.name || 'Anonymous')}</div>
        <div class="stars" aria-label="rating">${stars} <span class="muted">(${r.rating ?? '?'})</span></div>
      </div>
      <div class="date">${escapeHtml(r.date || '')}</div>
      <p class="text">${escapeHtml((r.text||'').toString().slice(0, 800))}</p>
      <p class="meta">
        ${escapeHtml(r.business || '')}
        ${r.city ? ' • ' + escapeHtml(r.city) : ''}
        ${r.price ? ' • ' + escapeHtml(r.price) : ''}
      </p>
    `;
    return el;
  }

  function escapeHtml(s){
    return String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  async function load(){
    try{
      const resp = await fetch('data.json', { cache: 'no-store' });
      if(!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      if(!data || !Array.isArray(data.reviews) || data.reviews.length === 0){
        root.innerHTML = '<p class="note">No reviews found in data.json (expected an array at data.reviews).</p>';
        return;
      }
      // render up to 50 reviews
      const frag = document.createDocumentFragment();
      data.reviews.slice(0, 50).forEach(r => frag.appendChild(createReviewCard(r)));
      root.replaceChildren(frag);
    }catch(err){
      console.error('Failed to load reviews:', err);
      root.innerHTML = '<p class="note">Failed to load <code>data.json</code>. Ensure the file is present next to <code>index.html</code>.</p>';
    }
  }

  load();
})();