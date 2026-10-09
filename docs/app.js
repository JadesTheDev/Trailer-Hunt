const $=id=>document.getElementById(id);let listings=[];const saved=new Set(JSON.parse(localStorage.getItem('trailer-hunt-favorites')||'[]'));const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);const clean=s=>String(s??'');function render(){const query=$('search').value.toLowerCase(),max=Number($('price').value)||Infinity,city=$('city').value,only=$('favorites').checked;let rows=listings.filter(x=>clean(x.title+' '+x.location+' '+x.city).toLowerCase().includes(query)&&Number(x.price)<=max&&(!city||x.city===city)&&(!only||saved.has(x.url)));const sort=$('sort').value;rows.sort((a,b)=>sort==='low'?a.price-b.price:sort==='high'?b.price-a.price:clean(b.last_seen).localeCompare(clean(a.last_seen)));$('status').textContent=rows.length+' listing'+(rows.length===1?'':'s')+' displayed';const target=$('results');target.replaceChildren();if(!rows.length){const msg=document.createElement('div');msg.className='empty';msg.textContent=listings.length?'No listings match your filters.':'No verified listings collected yet. This does not mean none are available on Craigslist.';target.append(msg);return;}for(const x of rows){const card=document.createElement('article');card.className='listing';const title=document.createElement('h2');title.textContent=x.title;const price=document.createElement('div');price.className='price-tag';price.textContent=money(x.price);const meta=document.createElement('div');meta.className='meta';meta.textContent=[x.location,x.city].filter(Boolean).join(' · ');const actions=document.createElement('div');actions.className='actions';const link=document.createElement('a');link.textContent='View Craigslist listing ↗';link.href=x.url;link.target='_blank';link.rel='noopener noreferrer';const heart=document.createElement('button');heart.type='button';heart.className='heart'+(saved.has(x.url)?' active':'');heart.textContent=saved.has(x.url)?'♥':'♡';heart.setAttribute('aria-label','Toggle favorite');heart.onclick=()=>{saved.has(x.url)?saved.delete(x.url):saved.add(x.url);localStorage.setItem('trailer-hunt-favorites',JSON.stringify([...saved]));render()};actions.append(link,heart);card.append(title,price,meta,actions);target.append(card)}}async function start(){try{const response=await fetch('data/listings.json',{cache:'no-store'});if(!response.ok)throw Error('Listing data unavailable');const data=await response.json();listings=Array.isArray(data)?data.filter(x=>x&&x.title&&Number.isFinite(Number(x.price))&&/^https:\/\/[^/]*craigslist\.org\//.test(x.url)):[];for(const city of [...new Set(listings.map(x=>x.city).filter(Boolean))].sort()){const option=document.createElement('option');option.value=city;option.textContent=city;$('city').append(option)}render()}catch(err){$('status').textContent='Could not load listing data.';$('results').textContent=err.message}}for(const id of ['search','price','city','sort','favorites'])$(id).addEventListener('input',render);start();
// External search hub: links only, no unauthorized scraping or imported results.
const sourceGroups=[
  {name:'Classifieds & marketplaces',sources:[
    ['Craigslist','craigslist.org'],['Facebook Marketplace','facebook.com/marketplace'],
    ['OfferUp','offerup.com'],['eBay','ebay.com'],['Nextdoor','nextdoor.com'],
    ['Oodle','oodle.com'],['Geebo','geebo.com'],['VarageSale','varagesale.com']
  ]},
  {name:'Trailers & equipment',sources:[
    ['Trailer Trader','trailertrader.com'],['Equipment Trader','equipmenttrader.com'],
    ['Machinery Trader','machinerytrader.com'],['Truck Paper','truckpaper.com'],
    ['EquipmentFacts','equipmentfacts.com'],['IronPlanet','ironplanet.com'],
    ['BigIron','bigiron.com'],['Purple Wave','purplewave.com']
  ]},
  {name:'Auctions & surplus',sources:[
    ['GovDeals','govdeals.com'],['Public Surplus','publicsurplus.com'],
    ['GSA Auctions','gsaauctions.gov'],['Ritchie Bros.','rbauction.com'],
    ['Proxibid','proxibid.com'],['HiBid','hibid.com'],
    ['AuctionZip','auctionzip.com'],['Municibid','municibid.com']
  ]},
  {name:'Local & alternative finds',sources:[
    ['EstateSales.net','estatesales.net'],['EstateSales.org','estatesales.org'],
    ['Search local trailer dealers','trailertrader.com'],
    ['Search local farm auctions','auctionzip.com'],
    ['Search used trailer frames','facebook.com/marketplace']
  ]}
];
function renderSources(){
  const target=$('source-links');if(!target)return;
  target.replaceChildren();
  const term=$('source-query').value;
  const region=$('source-region').value;
  for(const group of sourceGroups){
    const section=document.createElement('section');section.className='source-group';
    const heading=document.createElement('h3');heading.textContent=group.name;section.append(heading);
    const grid=document.createElement('div');grid.className='source-grid';
    for(const [name,domain] of group.sources){
      const a=document.createElement('a');a.className='source-link';a.target='_blank';a.rel='noopener noreferrer';
      const query='site:'+domain+' "'+term+'" '+region+' for sale';
      a.href='https://www.google.com/search?q='+encodeURIComponent(query);
      const title=document.createElement('strong');title.textContent=name+' ↗';
      const subtitle=document.createElement('small');subtitle.textContent='Search public listings';
      a.append(title,subtitle);grid.append(a);
    }
    section.append(grid);target.append(section);
  }
}
$('source-query').addEventListener('change',renderSources);
$('source-region').addEventListener('change',renderSources);
renderSources();
