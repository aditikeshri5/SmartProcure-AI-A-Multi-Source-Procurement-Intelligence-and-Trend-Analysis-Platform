const $ = id => document.getElementById(id);
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function money(value) {
  return new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(value);
}
document.querySelectorAll('[data-query]').forEach(btn => btn.addEventListener('click', () => {
  $('query').value = btn.dataset.query;
  $('query').focus();
}));
async function stats() {
  try {
    const response = await fetch('/api/stats');
    const data = await response.json();
    $('productCount').textContent = data.product_count;
    $('categoryCount').textContent = data.categories;
  } catch (_) {}
}
stats();
$('searchForm').addEventListener('submit', async event => {
  event.preventDefault();
  $('message').textContent = '';
  $('searchButton').disabled = true;
  $('searchButton').textContent = 'Finding matches…';
  try {
    const response = await fetch('/api/search', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:$('query').value,budget:$('budget').value,quantity:$('quantity').value})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Search failed');
    renderResults(data);
  } catch (error) {
    $('message').textContent = error.message;
  } finally {
    $('searchButton').disabled = false;
    $('searchButton').innerHTML = 'Find best matches <span>→</span>';
  }
});
function renderResults(data) {
  $('results').classList.remove('hidden');
  $('resultMeta').textContent = `Predicted category: ${data.predicted_category} · ${data.total_products_checked} catalogue records checked · ML: ${data.model.model}`;
  $('cards').innerHTML = data.recommendations.map((p,i)=>`
    <article class="product"><span class="rank">RECOMMENDATION #${i+1}</span>
    <h3>${escapeHtml(p.name)}</h3><div class="price">${money(p.price)}</div>
    <div class="specs">${escapeHtml(p.specs)}</div><div class="rating">★ ${Number(p.rating).toFixed(1)} / 5</div>
    <div class="supplier">${escapeHtml(p.supplier)} · ${escapeHtml(p.category)}</div>
    <div class="budget">${p.within_budget?'✓ Within unit budget':'Above unit budget'}</div>
    <div class="supplier">Estimated total: <b>${money(p.estimated_total)}</b></div></article>`).join('');
  const rows = [
    ['Product',...data.recommendations.map(p=>p.name)],
    ['Category',...data.recommendations.map(p=>p.category)],
    ['Unit price',...data.recommendations.map(p=>money(p.price))],
    ['Specifications',...data.recommendations.map(p=>p.specs)],
    ['Rating',...data.recommendations.map(p=>`★ ${Number(p.rating).toFixed(1)} / 5`)],
    ['Supplier',...data.recommendations.map(p=>p.supplier)],
    ['Estimated total',...data.recommendations.map(p=>money(p.estimated_total))]
  ];
  $('comparison').innerHTML = '<tbody>'+rows.map(row=>'<tr>'+row.map((cell,i)=>i===0?`<th>${escapeHtml(cell)}</th>`:`<td>${escapeHtml(cell)}</td>`).join('')+'</tr>').join('')+'</tbody>';
  $('notice').textContent = data.notice;
  $('results').scrollIntoView({behavior:'smooth',block:'start'});
}
$('scrapeForm').addEventListener('submit', async event => {
  event.preventDefault();
  $('scrapeOutput').classList.remove('hidden');
  $('scrapeOutput').textContent = 'Fetching page…';
  try {
    const response = await fetch('/api/scrape',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:$('scrapeUrl').value})});
    const data = await response.json();
    $('scrapeOutput').textContent = JSON.stringify(data,null,2);
  } catch (error) {$('scrapeOutput').textContent = error.message;}
});
