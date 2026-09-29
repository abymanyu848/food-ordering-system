/* CraveCart vanilla client. All pages use this one browser-native script. */
if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(regs) {
    for (var i = 0; i < regs.length; i++) regs[i].unregister();
  }).catch(function() {});
}

var API = '/api/v1';
var FALLBACK = '/uploads/foods/vegetarian.svg';
var userCache;

// API
function api(path, options) {
  options = options || {};
  var headers = new Headers(options.headers || {});
  var token = localStorage.getItem('access_token');
  if (token) headers.set('Authorization', 'Bearer ' + token);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  return fetch(API + path, Object.assign({}, options, { headers: headers })).then(function(response) {
    if (response.status === 204) return null;
    return response.text().then(function(text) {
      var payload = null;
      try { payload = text ? JSON.parse(text) : null; } catch (ignore) { payload = text; }
      if (!response.ok) {
        var detail = payload && typeof payload === 'object' ? (payload.detail || payload.message) : payload;
        var error = new Error(detail || 'Request failed (' + response.status + ')');
        error.status = response.status;
        throw error;
      }
      return payload;
    });
  });
}
function get(path, params) {
  var query = new URLSearchParams();
  Object.entries(params || {}).forEach(function(pair) { if (pair[1] !== undefined && pair[1] !== null && pair[1] !== '') query.set(pair[0], pair[1]); });
  return api(path + (query.toString() ? '?' + query.toString() : ''));
}
function send(method, path, body) { return api(path, { method: method, body: body === undefined ? undefined : JSON.stringify(body) }); }
function post(path, body) { return send('POST', path, body); }
function put(path, body) { return send('PUT', path, body); }
function patch(path, body) { return send('PATCH', path, body); }
function remove(path) { return send('DELETE', path); }

// Helpers, validation and notifications
function esc(value) { return String(value === null || value === undefined ? '' : value).replace(/[&<>"']/g, function(c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c]; }); }
function money(value) { return '₹' + Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }); }
function date(value) { return value ? new Date(value).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—'; }
function label(value) { return String(value || 'pending').replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); }); }
function pill(value) { return '<span class="status-pill status-' + esc(value) + '">' + esc(label(value)) + '</span>'; }
function idFromUrl() { return new URLSearchParams(location.search).get('id'); }
function formDataObject(form) {
  var result = {};
  new FormData(form).forEach(function(value, key) { result[key] = value; });
  form.querySelectorAll('input[type="checkbox"]').forEach(function(input) { result[input.name] = input.checked; });
  return result;
}
function formMessage(form, text, success) {
  var target = form.querySelector('[data-form-message]');
  if (target) { target.textContent = text || ''; target.classList.toggle('success', Boolean(success)); }
}
function fieldError(form, name, text) {
  var input = form.elements[name];
  var message = form.querySelector('#' + name.replace(/_/g, '-') + '-error');
  if (input) input.setAttribute('aria-invalid', text ? 'true' : 'false');
  if (message) message.textContent = text || '';
}
function clearFieldErrors(form) {
  ['full_name', 'email', 'phone', 'password', 'confirm_password'].forEach(function(name) { fieldError(form, name, ''); });
  formMessage(form, '');
}
function setupPasswordToggles() {
  document.querySelectorAll('[data-password-toggle]').forEach(function(button) {
    var input = document.getElementById(button.dataset.passwordToggle);
    if (!input) return;
    button.addEventListener('click', function() {
      var visible = input.type === 'text';
      input.type = visible ? 'password' : 'text';
      button.textContent = visible ? 'Show' : 'Hide';
      button.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
      button.setAttribute('aria-pressed', visible ? 'false' : 'true');
    });
  });
}
function validateRegister(form) {
  clearFieldErrors(form);
  var values = {
    full_name: form.elements.full_name.value.trim(),
    email: form.elements.email.value.trim(),
    phone: form.elements.phone.value.trim(),
    password: form.elements.password.value,
    confirm_password: form.elements.confirm_password.value
  };
  var firstInvalid = null;
  function invalid(name, message) { fieldError(form, name, message); if (!firstInvalid) firstInvalid = form.elements[name]; }
  if (values.full_name.length < 2) invalid('full_name', 'Enter your full name using at least 2 characters.');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) invalid('email', 'Enter a valid email address.');
  if (!/^[6-9]\d{9}$/.test(values.phone)) invalid('phone', 'Enter a valid 10-digit mobile number.');
  if (values.password.length < 8) invalid('password', 'Use at least 8 characters for your password.');
  if (!values.confirm_password) invalid('confirm_password', 'Re-enter your password.');
  else if (values.password !== values.confirm_password) invalid('confirm_password', 'Passwords do not match.');
  if (firstInvalid) { firstInvalid.focus(); return null; }
  return values;
}
function empty(text) { return '<div class="empty-state">' + text + '</div>'; }
function failure(error) { return '<div class="error-state">' + esc(error.message || error) + '</div>'; }
function notify(text, isError) {
  var region = document.querySelector('[data-toast-region]');
  if (!region) return;
  var toast = document.createElement('div');
  toast.className = 'toast' + (isError ? ' error' : '');
  toast.textContent = text;
  region.appendChild(toast);
  setTimeout(function() { toast.remove(); }, 3400);
}
function protect(roles) {
  if (!localStorage.getItem('access_token')) { location.href = '/login.html?next=' + encodeURIComponent(location.pathname + location.search); return false; }
  if (roles && roles.length && userCache && roles.indexOf(userCache.role) === -1) { document.querySelector('main').innerHTML = failure(new Error('You do not have permission to view this page.')); return false; }
  return true;
}
function asset(value, kind) { return value || (kind === 'restaurants' ? '/uploads/restaurants/fallback.jpg' : FALLBACK); }
function image(value, alt, kind) { return '<img src="' + esc(asset(value, kind)) + '" alt="' + esc(alt) + '" loading="lazy" onerror="this.hidden=true;this.nextElementSibling.hidden=false"><span class="image-fallback" hidden aria-hidden="true">Image unavailable</span>'; }
function cardRestaurant(item) {
  return '<article class="card"><a href="/restaurant.html?id=' + item.id + '"><div class="card-image">' + image(item.image, item.name, 'restaurants') + '</div><div class="card-body"><h3>' + esc(item.name) + '</h3><p>' + esc(item.description) + '</p><div class="card-meta"><span class="rating">★ ' + Number(item.rating || 0).toFixed(1) + '</span><span class="muted">' + esc((item.address || '').split(',')[0]) + '</span></div></div></a></article>';
}
function cardFood(item) {
  return '<article class="card"><a href="/food.html?id=' + item.id + '"><div class="card-image food-image">' + image(item.image, item.name) + '</div></a><div class="card-body"><h3><a href="/food.html?id=' + item.id + '">' + esc(item.name) + '</a></h3><p>' + esc(item.description) + '</p><div class="card-actions"><span class="price">' + money(item.price) + '</span><button class="button button-primary button-small" data-add-food="' + item.id + '" type="button">Add</button></div></div></article>';
}
function cardReview(item) { return '<div class="review-card"><strong>' + '★'.repeat(item.rating) + '☆'.repeat(5 - item.rating) + '</strong><p>' + esc(item.comment || 'No comment.') + '</p><small class="muted">' + date(item.created_at) + '</small></div>'; }

// Authentication and navigation
function loadUser() {
  if (userCache !== undefined) return Promise.resolve(userCache);
  if (!localStorage.getItem('access_token')) { userCache = null; return Promise.resolve(null); }
  return get('/users/me').then(function(user) { userCache = user; return user; }).catch(function() { localStorage.removeItem('access_token'); userCache = null; return null; });
}
function dashboardFor(role) { return role === 'admin' ? '/admin-dashboard.html' : role === 'restaurant' ? '/restaurant-dashboard.html' : role === 'delivery_person' ? '/delivery-dashboard.html' : '/'; }
function logout() { localStorage.removeItem('access_token'); userCache = null; location.href = '/'; }
function renderHeader(user) {
  var header = document.querySelector('[data-site-header]'); if (!header) return;
  var path = location.pathname;
  var auth = user ? '<span class="user-name">Hi, ' + esc(user.full_name.split(' ')[0]) + '</span><button class="button button-light button-small" data-logout type="button">Log out</button>' : '<a class="button button-dark button-small" href="/login.html">Sign in</a>';
  var work = user ? '<a href="' + dashboardFor(user.role) + '">Workspace</a>' : '';
  var extra = user ? '<a href="/orders.html">Orders</a><a href="/profile.html">Profile</a><a href="/cart.html">Cart</a>' : '';
  header.innerHTML = '<div class="nav-inner"><a class="brand" href="/"><span class="brand-mark">✦</span> CraveCart</a><button class="mobile-menu" data-mobile-menu type="button" aria-label="Open navigation" aria-expanded="false">☰</button><nav class="nav-links"><a class="' + (path === '/' ? 'active' : '') + '" href="/">Home</a><a href="/restaurants.html">Restaurants</a><a href="/foods.html">Dishes</a>' + extra + work + '</nav><div class="nav-user">' + auth + '</div></div>';
  var logoutButton = header.querySelector('[data-logout]'); if (logoutButton) logoutButton.addEventListener('click', logout);
  var menu = header.querySelector('[data-mobile-menu]'); if (menu) menu.addEventListener('click', function() { var open = header.querySelector('.nav-links').classList.toggle('open'); menu.setAttribute('aria-expanded', open ? 'true' : 'false'); menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation'); });
}
function renderFooter() { var footer = document.querySelector('[data-site-footer]'); if (footer) footer.innerHTML = '<div class="footer-inner"><span><strong>CraveCart</strong> · neighbourhood food, thoughtfully delivered.</span><span>Built for Nagercoil · COD accepted</span></div>'; }
function dashboardActionButtons() {
  document.querySelectorAll('[data-add-food]').forEach(function(button) {
    button.addEventListener('click', function() {
      if (!protect()) return;
      post('/cart/items', { food_id: Number(button.dataset.addFood), quantity: 1 }).then(function() { notify('Added to your cart.'); }).catch(function(error) {
        if (error.status === 409 && confirm('Your cart has dishes from another restaurant. Clear it and add this dish?')) post('/cart/items', { food_id: Number(button.dataset.addFood), quantity: 1, clear_existing: true }).then(function() { notify('Cart updated.'); }).catch(function(retry) { notify(retry.message, true); });
        else notify(error.message, true);
      });
    });
  });
}

// Home
function initHome() {
  Promise.all([get('/restaurants'), get('/foods', { available: true, sort: 'name' }), get('/categories')]).then(function(data) {
    document.querySelector('#home-restaurants').innerHTML = data[0].slice(0, 6).map(cardRestaurant).join('');
    document.querySelector('#home-foods').innerHTML = data[1].slice(0, 8).map(cardFood).join('');
    document.querySelector('#home-categories').innerHTML = [{ id: '', name: 'All dishes' }].concat(data[2]).map(function(item) { return '<a class="chip" href="/foods.html' + (item.id ? '?category_id=' + item.id : '') + '">' + esc(item.name) + '</a>'; }).join('');
    dashboardActionButtons();
  }).catch(function(error) { document.querySelector('#home-restaurants').innerHTML = failure(error); });
  document.querySelector('#home-search').addEventListener('submit', function(event) { event.preventDefault(); location.href = '/foods.html?search=' + encodeURIComponent(new FormData(event.currentTarget).get('search')); });
}

// Restaurants, foods and details
function initRestaurants() {
  var grid = document.querySelector('#restaurant-grid'), items = [];
  function draw() {
    var term = document.querySelector('#restaurant-search').value.toLowerCase();
    var sort = document.querySelector('#restaurant-sort').value;
    var list = items.filter(function(item) { return (item.name + ' ' + item.description + ' ' + item.address).toLowerCase().indexOf(term) >= 0; });
    list.sort(function(a, b) { return sort === 'rating' ? b.rating - a.rating : a.name.localeCompare(b.name); });
    grid.innerHTML = list.length ? list.map(cardRestaurant).join('') : empty('No restaurants match that search.');
  }
  get('/restaurants').then(function(result) { items = result; draw(); }).catch(function(error) { grid.innerHTML = failure(error); });
  document.querySelector('#restaurant-search').addEventListener('input', draw);
  document.querySelector('#restaurant-sort').addEventListener('change', draw);
}
function initFoods() {
  var params = new URLSearchParams(location.search), search = document.querySelector('#food-search'), restaurant = document.querySelector('#food-restaurant'), category = document.querySelector('#food-category'), sort = document.querySelector('#food-sort');
  search.value = params.get('search') || '';
  Promise.all([get('/restaurants'), get('/categories')]).then(function(data) {
    restaurant.innerHTML += data[0].map(function(item) { return '<option value="' + item.id + '">' + esc(item.name) + '</option>'; }).join('');
    category.innerHTML += data[1].map(function(item) { return '<option value="' + item.id + '">' + esc(item.name) + '</option>'; }).join('');
    restaurant.value = params.get('restaurant_id') || ''; category.value = params.get('category_id') || ''; sort.value = params.get('sort') || 'name'; draw();
  }).catch(function(error) { document.querySelector('#food-grid').innerHTML = failure(error); });
  document.querySelector('#food-filter').addEventListener('click', draw);
  function draw() {
    var grid = document.querySelector('#food-grid'); grid.innerHTML = '<div class="loading-state">Refreshing the menu…</div>';
    get('/foods', { search: search.value, restaurant_id: restaurant.value, category_id: category.value, sort: sort.value, available: true }).then(function(items) { grid.innerHTML = items.length ? items.map(cardFood).join('') : empty('No dishes match those filters.'); dashboardActionButtons(); }).catch(function(error) { grid.innerHTML = failure(error); });
  }
}
function initRestaurant() {
  var id = idFromUrl(), target = document.querySelector('#restaurant-detail');
  if (!id) { target.innerHTML = failure(new Error('Restaurant id is missing.')); return; }
  Promise.all([get('/restaurants/' + id), get('/foods', { restaurant_id: id, available: true }), get('/reviews', { restaurant_id: id })]).then(function(data) {
    var restaurant = data[0], foods = data[1], reviews = data[2];
    document.title = restaurant.name + ' · CraveCart';
    target.innerHTML = '<div class="detail-hero"><div class="detail-image">' + image(restaurant.image, restaurant.name, 'restaurants') + '</div><div class="detail-copy"><p class="eyebrow">Restaurant</p><h1>' + esc(restaurant.name) + '</h1><p class="detail-description">' + esc(restaurant.description) + '</p><p class="muted">★ ' + Number(restaurant.rating || 0).toFixed(1) + ' · ' + esc(restaurant.address) + ' · ' + esc(restaurant.opening_time) + ' – ' + esc(restaurant.closing_time) + '</p><div class="detail-actions"><a class="button button-primary" href="/foods.html?restaurant_id=' + restaurant.id + '">Browse menu</a><a class="button button-light" href="/restaurants.html">Back to list</a></div></div></div><div class="detail-grid"><section><div class="section-heading"><h2>Menu</h2><span class="muted">' + foods.length + ' available dishes</span></div><div class="card-grid food-grid">' + (foods.length ? foods.map(cardFood).join('') : empty('This kitchen is between menus right now.')) + '</div></section><section class="panel"><div class="section-heading tight"><h2>Reviews</h2></div>' + (reviews.length ? reviews.map(cardReview).join('') : empty('No reviews yet.')) + '</section></div>';
    dashboardActionButtons();
  }).catch(function(error) { target.innerHTML = failure(error); });
}
function initFood() {
  var id = idFromUrl(), target = document.querySelector('#food-detail');
  if (!id) { target.innerHTML = failure(new Error('Food id is missing.')); return; }
  Promise.all([get('/foods/' + id), get('/reviews', { food_id: id })]).then(function(data) { return Promise.all([data[0], get('/restaurants/' + data[0].restaurant_id), data[1]]); }).then(function(data) {
    var food = data[0], restaurant = data[1], reviews = data[2];
    target.innerHTML = '<div class="detail-hero"><div class="detail-image">' + image(food.image, food.name) + '</div><div class="detail-copy"><p class="eyebrow">From ' + esc(restaurant.name) + '</p><h1>' + esc(food.name) + '</h1><p class="detail-description">' + esc(food.description) + '</p><p class="price">' + money(food.price) + '</p><div class="detail-actions"><button class="button button-primary" data-add-food="' + food.id + '" type="button">Add to cart</button><a class="button button-light" href="/restaurant.html?id=' + restaurant.id + '">Back to restaurant</a></div></div></div><div class="detail-grid"><section class="panel"><h2>About this dish</h2><p class="lede">' + esc(food.description) + ' Available now from ' + esc(restaurant.name) + '.</p></section><section class="panel"><h2>Reviews</h2>' + (reviews.length ? reviews.map(cardReview).join('') : empty('No reviews yet.')) + '</section></div>';
    dashboardActionButtons();
  }).catch(function(error) { target.innerHTML = failure(error); });
}

// Cart and checkout
function initCart() {
  if (!protect()) return;
  var target = document.querySelector('#cart-content');
  get('/cart').then(function(cart) {
    if (!cart.items.length) { target.innerHTML = empty('Your cart is waiting for something delicious. <a class="text-link" href="/foods.html">Browse dishes →</a>'); return; }
    target.innerHTML = '<div class="cart-layout"><section class="panel"><div class="section-heading tight"><h2>' + cart.items.length + ' item' + (cart.items.length === 1 ? '' : 's') + '</h2><button class="button button-light button-small" id="clear-cart" type="button">Clear cart</button></div>' + cart.items.map(function(item) { return '<div class="cart-item"><div class="cart-thumb">✦</div><div class="cart-item-main"><h3>' + esc(item.food.name) + '</h3><p>' + money(item.food.price) + ' each</p></div><div class="qty-control"><button data-qty="' + item.id + '" data-value="' + (item.quantity - 1) + '" type="button">−</button><strong>' + item.quantity + '</strong><button data-qty="' + item.id + '" data-value="' + (item.quantity + 1) + '" type="button">+</button></div><span class="price">' + money(Number(item.food.price) * item.quantity) + '</span><button class="button button-danger button-small" data-remove-item="' + item.id + '" type="button">Remove</button></div>'; }).join('') + '</section><aside class="panel summary-panel"><p class="eyebrow">Ready when you are</p><h2>Order summary</h2><div class="summary-row"><span>Items</span><strong>' + money(cart.total_price) + '</strong></div><div class="summary-row"><span>Delivery</span><strong>COD</strong></div><div class="summary-row total"><span>Total</span><strong>' + money(cart.total_price) + '</strong></div><a class="button button-primary full-button" href="/checkout.html">Continue to checkout</a></aside></div>';
    document.querySelector('#clear-cart').addEventListener('click', function() { remove('/cart').then(initCart); });
    document.querySelectorAll('[data-qty]').forEach(function(button) { button.addEventListener('click', function() { var value = Number(button.dataset.value); (value < 1 ? remove('/cart/items/' + button.dataset.qty) : put('/cart/items/' + button.dataset.qty, { quantity: value })).then(initCart); }); });
    document.querySelectorAll('[data-remove-item]').forEach(function(button) { button.addEventListener('click', function() { remove('/cart/items/' + button.dataset.removeItem).then(initCart); }); });
  }).catch(function(error) { target.innerHTML = failure(error); });
}
function initCheckout() {
  if (!protect()) return;
  var target = document.querySelector('#checkout-content');
  Promise.all([get('/cart'), get('/users/me/addresses')]).then(function(data) {
    var cart = data[0], addresses = data[1];
    if (!cart.items.length) { target.innerHTML = empty('Your cart is empty. <a class="text-link" href="/foods.html">Choose a dish first →</a>'); return; }
    target.innerHTML = '<div class="checkout-layout"><section class="panel"><h2>Delivery address</h2><form id="checkout-form" class="stack-form">' + (addresses.length ? '<div class="address-choice">' + addresses.map(function(address, index) { return '<label class="address-option"><input type="radio" name="saved_address" value="' + address.id + '" ' + (index === 0 ? 'checked' : '') + '><span>' + esc(address.address_line) + ', ' + esc(address.city) + ', ' + esc(address.state) + ' — ' + esc(address.pincode) + '</span></label>'; }).join('') + '<label class="address-option"><input type="radio" name="saved_address" value="new"><span>Use a new address</span></label></div>' : '') + '<div id="new-address-fields" class="' + (addresses.length ? 'hidden' : '') + ' stack-form"><label>Address line<input name="address_line" minlength="5" placeholder="House, street, landmark"></label><div class="form-pair"><label>City<input name="city"></label><label>State<input name="state"></label></div><label>Pincode<input name="pincode" pattern="[0-9]{6}"></label></div><div class="cod-note"><span>▣</span><span><strong>Cash on delivery</strong><br><small>Pay when your food arrives.</small></span></div><button class="button button-primary full-button" type="submit">Place COD order</button><div class="form-message" data-form-message></div></form></section><aside class="panel summary-panel"><p class="eyebrow">From your cart</p><h2>Order summary</h2>' + cart.items.map(function(item) { return '<div class="summary-row"><span>' + item.quantity + ' × ' + esc(item.food.name) + '</span><strong>' + money(Number(item.food.price) * item.quantity) + '</strong></div>'; }).join('') + '<div class="summary-row total"><span>Total</span><strong>' + money(cart.total_price) + '</strong></div></aside></div>';
    var form = document.querySelector('#checkout-form'), fields = document.querySelector('#new-address-fields');
    form.querySelectorAll('[name="saved_address"]').forEach(function(radio) { radio.addEventListener('change', function() { fields.classList.toggle('hidden', radio.value !== 'new' || !radio.checked); }); });
    form.addEventListener('submit', function(event) { event.preventDefault(); var selected = form.querySelector('[name="saved_address"]:checked'), address = ''; if (selected && selected.value !== 'new') { var saved = addresses.find(function(item) { return String(item.id) === selected.value; }); address = saved.address_line + ', ' + saved.city + ', ' + saved.state + ' - ' + saved.pincode; } else { var data = formDataObject(form); address = (data.address_line || '') + ', ' + (data.city || '') + ', ' + (data.state || '') + ' - ' + (data.pincode || ''); } if (address.replace(/[, -]/g, '').length < 10) { formMessage(form, 'Please provide a complete delivery address.'); return; } post('/orders', { delivery_address: address }).then(function(order) { location.href = '/order.html?id=' + order.id; }).catch(function(error) { formMessage(form, error.message); }); });
  }).catch(function(error) { target.innerHTML = failure(error); });
}

// Orders and reviews
function orderCard(order) { return '<article class="order-card"><div><p class="eyebrow">Order #' + order.id + ' · ' + date(order.created_at) + '</p><h3>' + order.items.map(function(item) { return item.quantity + ' × ' + esc(item.name); }).join(', ') + '</h3><p>' + esc(order.delivery_address) + '</p><p class="price">' + money(order.total_price) + '</p></div><div class="card-actions">' + pill(order.status) + '<a class="button button-light button-small" href="/order.html?id=' + order.id + '">View details</a>' + (['pending', 'accepted', 'preparing'].indexOf(order.status) >= 0 ? '<button class="button button-danger button-small" data-cancel-order="' + order.id + '" type="button">Cancel</button>' : '') + '</div></article>'; }
function initOrders() {
  if (!protect()) return;
  var target = document.querySelector('#orders-content');
  get('/orders').then(function(orders) { target.innerHTML = orders.length ? orders.map(orderCard).join('') : empty('No orders yet. <a href="/foods.html">Find something good →</a>'); document.querySelectorAll('[data-cancel-order]').forEach(function(button) { button.addEventListener('click', function() { if (confirm('Cancel this order?')) post('/orders/' + button.dataset.cancelOrder + '/cancel').then(initOrders).catch(function(error) { notify(error.message, true); }); }); }); }).catch(function(error) { target.innerHTML = failure(error); });
}
function initOrder() {
  if (!protect()) return;
  var id = idFromUrl(), target = document.querySelector('#order-detail'); if (!id) { target.innerHTML = failure(new Error('Order id is missing.')); return; }
  get('/orders/' + id).then(function(order) {
    var steps = ['pending', 'accepted', 'preparing', 'ready', 'assigned', 'out_for_delivery', 'delivered'], current = steps.indexOf(order.status);
    target.innerHTML = '<div class="page-intro compact"><p class="eyebrow">Order #' + order.id + ' · ' + date(order.created_at) + '</p><h1>On its way to you.</h1><p class="lede">' + pill(order.status) + ' <span class="muted">' + esc(order.delivery_address) + '</span></p></div><div class="detail-grid"><section class="panel"><h2>Progress</h2><div class="order-timeline">' + steps.map(function(step, index) { return '<div class="timeline-step ' + (index <= current ? 'active' : '') + '">' + label(step) + '</div>'; }).join('') + '</div><h2>Your items</h2><div class="order-items">' + order.items.map(function(item) { return '<div class="order-line"><span>' + item.quantity + ' × ' + esc(item.name) + '</span><strong>' + money(Number(item.price) * item.quantity) + '</strong></div>'; }).join('') + '</div><div class="summary-row total"><span>Total · Cash on delivery</span><strong>' + money(order.total_price) + '</strong></div>' + (['pending', 'accepted', 'preparing'].indexOf(order.status) >= 0 ? '<button class="button button-danger" id="order-cancel" type="button">Cancel order</button>' : '') + '</section><section class="panel"><h2>Leave a review</h2><p class="muted">Tell the kitchen what you thought once your order arrives.</p><form id="review-form" class="stack-form"><input type="hidden" name="restaurant_id" value="' + order.restaurant_id + '"><label>Rating<select name="rating" required><option value="5">★★★★★ · Loved it</option><option value="4">★★★★☆ · Great</option><option value="3">★★★☆☆ · Good</option><option value="2">★★☆☆☆ · Needs work</option><option value="1">★☆☆☆☆ · Not for me</option></select></label><label>Comment<textarea name="comment" maxlength="1000" placeholder="What stood out?"></textarea></label><button class="button button-primary" type="submit">Submit review</button><div class="form-message" data-form-message></div></form></section></div>';
    var cancel = document.querySelector('#order-cancel'); if (cancel) cancel.addEventListener('click', function() { post('/orders/' + id + '/cancel').then(initOrder).catch(function(error) { notify(error.message, true); }); });
    document.querySelector('#review-form').addEventListener('submit', function(event) { event.preventDefault(); var form = event.currentTarget; post('/reviews', formDataObject(form)).then(function() { formMessage(form, 'Thanks for the review.', true); }).catch(function(error) { formMessage(form, error.message); }); });
  }).catch(function(error) { target.innerHTML = failure(error); });
}

// Profile
function initProfile() {
  if (!protect()) return;
  Promise.all([loadUser(), get('/users/me/addresses')]).then(function(data) {
    var user = data[0], addresses = data[1], profile = document.querySelector('#profile-form');
    profile.elements.full_name.value = user.full_name || ''; profile.elements.phone.value = user.phone || '';
    profile.addEventListener('submit', function(event) { event.preventDefault(); put('/users/me', { full_name: profile.elements.full_name.value, phone: profile.elements.phone.value }).then(function(result) { userCache = result; renderHeader(result); formMessage(profile, 'Profile saved.', true); }).catch(function(error) { formMessage(profile, error.message); }); });
    drawAddresses();
    document.querySelector('#address-form').addEventListener('submit', function(event) { event.preventDefault(); var form = event.currentTarget; post('/users/me/addresses', formDataObject(form)).then(function(address) { addresses.push(address); form.reset(); drawAddresses(); notify('Address saved.'); }).catch(function(error) { formMessage(form, error.message); }); });
    function drawAddresses() { var target = document.querySelector('#address-list'); target.innerHTML = addresses.length ? addresses.map(function(item) { return '<div class="address-card"><p>' + esc(item.address_line) + ', ' + esc(item.city) + ', ' + esc(item.state) + ' — ' + esc(item.pincode) + '</p><button class="button button-danger button-small" data-delete-address="' + item.id + '" type="button">Delete</button></div>'; }).join('') : empty('No saved addresses yet.'); target.querySelectorAll('[data-delete-address]').forEach(function(button) { button.addEventListener('click', function() { remove('/users/me/addresses/' + button.dataset.deleteAddress).then(function() { addresses.splice(addresses.findIndex(function(item) { return String(item.id) === button.dataset.deleteAddress; }), 1); drawAddresses(); }); }); }); }
  }).catch(function(error) { document.querySelector('main').insertAdjacentHTML('beforeend', failure(error)); });
}

// File uploads
function uploadImage(path, file) {
  var body = new FormData();
  body.append('image', file);
  return api(path, { method: 'POST', body: body }).then(function(result) { return result.url; });
}

// Restaurant dashboard
function nextStatus(value) { return { pending: 'accepted', accepted: 'preparing', preparing: 'ready' }[value]; }
function initRestaurantDashboard() {
  if (!protect(['restaurant'])) return;
  Promise.all([get('/restaurant/me'), get('/restaurant/foods'), get('/categories')]).then(function(data) {
    var restaurant = data[0], foods = data[1], categories = data[2], profile = document.querySelector('#restaurant-profile-form'), foodForm = document.querySelector('#restaurant-food-form');
    ['name', 'description', 'address', 'phone'].forEach(function(key) { profile.elements[key].value = restaurant[key] || ''; }); profile.elements.opening_time.value = String(restaurant.opening_time || '').slice(0, 5); profile.elements.closing_time.value = String(restaurant.closing_time || '').slice(0, 5);
    profile.addEventListener('submit', function(event) { event.preventDefault(); var body = formDataObject(profile); body.opening_time += ':00'; body.closing_time += ':00'; body.rating = restaurant.rating; body.is_active = restaurant.is_active; put('/restaurant/me', body).then(function() { formMessage(profile, 'Restaurant saved.', true); }).catch(function(error) { formMessage(profile, error.message); }); });
    foodForm.elements.category_id.innerHTML = categories.map(function(item) { return '<option value="' + item.id + '">' + esc(item.name) + '</option>'; }).join('');
    document.querySelector('#show-food-form').addEventListener('click', function() { foodForm.reset(); foodForm.elements.id.value = ''; foodForm.classList.toggle('hidden'); });
    function drawFoods() {
      document.querySelector('#restaurant-foods').innerHTML = foods.length ? '<table><thead><tr><th>Dish</th><th>Price</th><th>Availability</th><th></th></tr></thead><tbody>' + foods.map(function(item) { return '<tr><td>' + esc(item.name) + '</td><td>' + money(item.price) + '</td><td>' + (item.is_available ? 'Available' : 'Hidden') + '</td><td><button class="button button-light button-small" data-edit-food="' + item.id + '" type="button">Edit</button> <button class="button button-danger button-small" data-delete-food="' + item.id + '" type="button">Delete</button></td></tr>'; }).join('') + '</tbody></table>' : empty('No menu items yet.');
      document.querySelectorAll('[data-edit-food]').forEach(function(button) { button.addEventListener('click', function() { var item = foods.find(function(food) { return food.id === Number(button.dataset.editFood); }); Object.entries(item).forEach(function(pair) { if (foodForm.elements[pair[0]]) foodForm.elements[pair[0]].value = pair[1]; }); foodForm.elements.is_available.checked = item.is_available; foodForm.classList.remove('hidden'); }); });
      document.querySelectorAll('[data-delete-food]').forEach(function(button) { button.addEventListener('click', function() { if (confirm('Delete this dish?')) remove('/restaurant/foods/' + button.dataset.deleteFood).then(function() { foods.splice(foods.findIndex(function(item) { return item.id === Number(button.dataset.deleteFood); }), 1); drawFoods(); }); }); });
    }
    drawFoods();
    foodForm.addEventListener('submit', function(event) { event.preventDefault(); var body = formDataObject(foodForm), id = body.id, file = foodForm.elements.image_file.files[0]; delete body.id; delete body.image_file; body.category_id = Number(body.category_id); body.price = Number(body.price); (file ? uploadImage('/restaurant/uploads/foods', file) : Promise.resolve(body.image || null)).then(function(url) { if (url) body.image = url; return id ? put('/restaurant/foods/' + id, body) : post('/restaurant/foods', body); }).then(function(result) { var index = foods.findIndex(function(item) { return item.id === result.id; }); if (index >= 0) foods[index] = result; else foods.push(result); foodForm.classList.add('hidden'); drawFoods(); notify('Menu updated.'); }).catch(function(error) { formMessage(foodForm, error.message); }); });
    function drawOrders() { get('/restaurant/orders', { status_filter: document.querySelector('#restaurant-order-status').value }).then(function(orders) { var target = document.querySelector('#restaurant-orders'); target.innerHTML = orders.length ? orders.map(function(order) { var next = nextStatus(order.status); return '<div class="dashboard-order"><div><strong>Order #' + order.id + '</strong> ' + pill(order.status) + '<p>' + order.items.map(function(item) { return item.quantity + ' × ' + esc(item.name); }).join(', ') + ' · ' + money(order.total_price) + '</p><p>' + esc(order.delivery_address) + '</p></div><div class="dashboard-order-actions">' + (next ? '<button class="button button-primary button-small" data-restaurant-status="' + order.id + '" data-next-status="' + next + '" type="button">' + label(next) + '</button>' : '') + '<a class="button button-light button-small" href="/order.html?id=' + order.id + '">View</a></div></div>'; }).join('') : empty('No orders in this view.'); target.querySelectorAll('[data-restaurant-status]').forEach(function(button) { button.addEventListener('click', function() { patch('/restaurant/orders/' + button.dataset.restaurantStatus + '/status', { status: button.dataset.nextStatus }).then(function() { drawOrders(); }).catch(function(error) { notify(error.message, true); }); }); }); }); }
    document.querySelector('#restaurant-order-status').addEventListener('change', drawOrders); drawOrders();
  }).catch(function(error) { document.querySelector('main').insertAdjacentHTML('beforeend', failure(error)); });
}

// Delivery dashboard
function initDeliveryDashboard() {
  if (!protect(['delivery_person'])) return;
  get('/delivery/me').then(function(delivery) {
    var form = document.querySelector('#delivery-profile-form'); form.elements.phone.value = delivery.phone || ''; form.elements.vehicle_type.value = delivery.vehicle_type || ''; form.elements.vehicle_number.value = delivery.vehicle_number || ''; form.elements.is_available.checked = delivery.is_available;
    form.addEventListener('submit', function(event) { event.preventDefault(); put('/delivery/me', formDataObject(form)).then(function() { formMessage(form, 'Delivery profile saved.', true); }).catch(function(error) { formMessage(form, error.message); }); });
    function draw() {
      Promise.all([get('/delivery/orders'), get('/delivery/orders/available')]).then(function(data) {
        document.querySelector('#delivery-orders').innerHTML = data[0].length ? data[0].map(function(order) { var action = { assigned: ['accept', 'Accept order'], accepted: ['pickup', 'Mark picked up'], picked_up: ['out-for-delivery', 'Out for delivery'], out_for_delivery: ['delivered', 'Mark delivered'] }[order.delivery_status]; return '<div class="dashboard-order"><div><strong>Order #' + order.id + '</strong> ' + pill(order.delivery_status) + '<p>' + order.items.map(function(item) { return item.quantity + ' × ' + esc(item.name); }).join(', ') + '</p><p>' + esc(order.delivery_address) + '</p></div><div class="dashboard-order-actions">' + (action ? '<button class="button button-primary button-small" data-delivery-action="' + order.id + '" data-action="' + action[0] + '">' + action[1] + '</button>' : '') + '</div></div>'; }).join('') : empty('No assigned deliveries yet.');
        document.querySelector('#available-orders').innerHTML = data[1].length ? data[1].map(function(order) { return '<div class="dashboard-order"><strong>Order #' + order.id + '</strong><span class="status-pill status-ready">Waiting for assignment</span></div>'; }).join('') : empty('No ready orders are waiting for assignment.');
        document.querySelectorAll('[data-delivery-action]').forEach(function(button) { button.addEventListener('click', function() { post('/delivery/orders/' + button.dataset.deliveryAction + '/' + button.dataset.action).then(draw).catch(function(error) { notify(error.message, true); }); }); });
      }).catch(function(error) { document.querySelector('#delivery-orders').innerHTML = failure(error); });
    }
    document.querySelector('#delivery-refresh').addEventListener('click', draw); draw();
  }).catch(function(error) { document.querySelector('main').insertAdjacentHTML('beforeend', failure(error)); });
}

// Admin dashboard
function initAdminDashboard() {
  if (!protect(['admin'])) return;
  var foodForm = document.querySelector('#admin-food-form');
  function draw() {
    Promise.all([get('/admin/reports'), get('/admin/orders'), get('/admin/restaurants'), get('/categories'), get('/admin/delivery-persons'), get('/admin/users'), get('/admin/foods')]).then(function(data) {
      var reports = data[0], orders = data[1], restaurants = data[2], categories = data[3], people = data[4], users = data[5], foods = data[6];
      document.querySelector('#admin-metrics').innerHTML = [['Users', reports.total_users], ['Restaurants', reports.total_restaurants], ['Dishes', reports.total_foods], ['Revenue', money(reports.total_revenue)]].map(function(item) { return '<div class="metric"><small>' + item[0] + '</small><strong>' + item[1] + '</strong></div>'; }).join('');
      document.querySelector('#admin-categories').innerHTML = categories.map(function(item) { return '<div class="dashboard-order"><strong>' + esc(item.name) + '</strong><button class="button button-danger button-small" data-delete-category="' + item.id + '">Delete</button></div>'; }).join('');
      document.querySelector('#admin-delivery').innerHTML = people.map(function(item) { return '<div class="dashboard-order"><div><strong>#' + item.id + ' · ' + esc(item.vehicle_type) + '</strong><p>' + esc(item.vehicle_number) + '</p></div><span class="status-pill status-ready">' + (item.is_available ? 'Available' : 'Busy') + '</span></div>'; }).join('');
      document.querySelector('#admin-restaurants').innerHTML = '<table><thead><tr><th>Name</th><th>Rating</th><th>Phone</th><th>Address</th></tr></thead><tbody>' + restaurants.map(function(item) { return '<tr><td>' + esc(item.name) + '</td><td>★ ' + Number(item.rating || 0).toFixed(1) + '</td><td>' + esc(item.phone) + '</td><td>' + esc(item.address) + '</td></tr>'; }).join('') + '</tbody></table>';
      document.querySelector('#admin-orders').innerHTML = '<table><thead><tr><th>Order</th><th>Status</th><th>Total</th><th>Delivery</th><th>Action</th></tr></thead><tbody>' + orders.map(function(order) { var select = order.status === 'ready' && !order.delivery_person_id ? '<select data-assign-order="' + order.id + '"><option value="">Assign…</option>' + people.filter(function(person) { return person.is_available; }).map(function(person) { return '<option value="' + person.id + '">Person #' + person.id + '</option>'; }).join('') + '</select>' : '—'; return '<tr><td>#' + order.id + '</td><td>' + pill(order.status) + '</td><td>' + money(order.total_price) + '</td><td>' + (order.delivery_person_id ? 'Person #' + order.delivery_person_id : 'Unassigned') + '</td><td>' + select + '</td></tr>'; }).join('') + '</tbody></table>';
      var roles = ['customer', 'restaurant', 'delivery_person', 'admin'];
      document.querySelector('#admin-users').innerHTML = '<table><thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>' + users.map(function(user) { return '<tr><td>' + user.id + '</td><td>' + esc(user.full_name) + '</td><td>' + esc(user.email) + '</td><td><select data-user-role="' + user.id + '">' + roles.map(function(role) { return '<option value="' + role + '"' + (user.role === role ? ' selected' : '') + '>' + role + '</option>'; }).join('') + '</select></td><td>' + (user.is_active ? '<span class="status-pill status-ready">Active</span>' : '<span class="status-pill status-cancelled">Disabled</span>') + '</td><td><button class="button button-light button-small" data-toggle-user="' + user.id + '" data-active="' + (user.is_active ? '1' : '0') + '" type="button">' + (user.is_active ? 'Disable' : 'Enable') + '</button></td></tr>'; }).join('') + '</tbody></table>';
      document.querySelector('#admin-foods').innerHTML = foods.length ? '<table><thead><tr><th>Dish</th><th>Restaurant</th><th>Category</th><th>Price</th><th>Availability</th><th></th></tr></thead><tbody>' + foods.map(function(item) { var restaurant = restaurants.find(function(row) { return row.id === item.restaurant_id; }); var category = categories.find(function(row) { return row.id === item.category_id; }); return '<tr><td>' + esc(item.name) + '</td><td>' + esc(restaurant ? restaurant.name : '—') + '</td><td>' + esc(category ? category.name : '—') + '</td><td>' + money(item.price) + '</td><td>' + (item.is_available ? 'Available' : 'Hidden') + '</td><td><button class="button button-light button-small" data-edit-food="' + item.id + '" type="button">Edit</button> <button class="button button-danger button-small" data-delete-food="' + item.id + '" type="button">Delete</button></td></tr>'; }).join('') + '</tbody></table>' : empty('No dishes yet.');
      foodForm.elements.category_id.innerHTML = categories.map(function(item) { return '<option value="' + item.id + '">' + esc(item.name) + '</option>'; }).join('');
      foodForm.elements.restaurant_id.innerHTML = restaurants.map(function(item) { return '<option value="' + item.id + '">' + esc(item.name) + '</option>'; }).join('');

      document.querySelectorAll('[data-delete-category]').forEach(function(button) { button.addEventListener('click', function() { if (confirm('Delete this category?')) remove('/categories/' + button.dataset.deleteCategory).then(draw).catch(function(error) { notify(error.message, true); }); }); });
      document.querySelectorAll('[data-user-role]').forEach(function(select) { select.addEventListener('change', function() { patch('/admin/users/' + select.dataset.userRole, { role: select.value }).then(draw).catch(function(error) { notify(error.message, true); draw(); }); }); });
      document.querySelectorAll('[data-toggle-user]').forEach(function(button) { button.addEventListener('click', function() { var active = button.dataset.active === '1'; if (active && !confirm('Disable this account?')) return; patch('/admin/users/' + button.dataset.toggleUser, { is_active: !active }).then(draw).catch(function(error) { notify(error.message, true); }); }); });
      document.querySelectorAll('[data-edit-food]').forEach(function(button) { button.addEventListener('click', function() { var item = foods.find(function(food) { return food.id === Number(button.dataset.editFood); }); formMessage(foodForm, ''); foodForm.elements.id.value = item.id; foodForm.elements.name.value = item.name; foodForm.elements.description.value = item.description; foodForm.elements.price.value = item.price; foodForm.elements.category_id.value = item.category_id; foodForm.elements.restaurant_id.value = item.restaurant_id; foodForm.elements.image.value = item.image || ''; foodForm.elements.is_available.checked = item.is_available; foodForm.classList.remove('hidden'); foodForm.scrollIntoView({ behavior: 'smooth', block: 'center' }); }); });
      document.querySelectorAll('[data-delete-food]').forEach(function(button) { button.addEventListener('click', function() { if (confirm('Delete this dish?')) remove('/foods/' + button.dataset.deleteFood).then(draw).catch(function(error) { notify(error.message, true); }); }); });

      document.querySelectorAll('[data-assign-order]').forEach(function(select) { select.addEventListener('change', function() { if (select.value) patch('/admin/orders/' + select.dataset.assignOrder + '/assign-delivery', { delivery_person_id: Number(select.value) }).then(draw).catch(function(error) { notify(error.message, true); }); }); });
    }).catch(function(error) { document.querySelector('#admin-orders').innerHTML = failure(error); });
  }
  document.querySelector('#category-form').addEventListener('submit', function(event) { event.preventDefault(); var form = event.currentTarget; post('/categories', { name: form.elements.name.value }).then(function() { form.reset(); draw(); }).catch(function(error) { formMessage(form, error.message); }); });
  document.querySelector('#admin-show-food-form').addEventListener('click', function() { foodForm.reset(); foodForm.elements.id.value = ''; foodForm.elements.image.value = ''; formMessage(foodForm, ''); foodForm.classList.toggle('hidden'); });
  foodForm.addEventListener('submit', function(event) { event.preventDefault(); var body = formDataObject(foodForm), id = body.id, file = foodForm.elements.image_file.files[0]; delete body.id; delete body.image_file; body.category_id = Number(body.category_id); body.restaurant_id = Number(body.restaurant_id); body.price = Number(body.price); (file ? uploadImage('/uploads/foods', file) : Promise.resolve(body.image || null)).then(function(url) { if (url) body.image = url; return id ? put('/foods/' + id, body) : post('/foods', body); }).then(function() { foodForm.classList.add('hidden'); draw(); notify('Dish saved.'); }).catch(function(error) { formMessage(foodForm, error.message); }); });

  document.querySelector('#admin-refresh').addEventListener('click', draw); draw();
}

// Login and register
function initLogin() {
  var form = document.querySelector('#login-form');
  form.addEventListener('submit', function(event) { event.preventDefault(); if (!form.reportValidity()) return; post('/auth/login', formDataObject(form)).then(function(result) { localStorage.setItem('access_token', result.access_token); return get('/users/me'); }).then(function(user) { userCache = user; location.href = new URLSearchParams(location.search).get('next') || dashboardFor(user.role); }).catch(function(error) { formMessage(form, error.message); }); });
}
function initRegister() {
  var form = document.querySelector('#register-form');
  form.querySelectorAll('input').forEach(function(input) { input.addEventListener('input', function() { if (input.name === 'phone') input.value = input.value.replace(/\D/g, '').slice(0, 10); fieldError(form, input.name, ''); if (input.name === 'password' || input.name === 'confirm_password') fieldError(form, 'confirm_password', ''); }); });
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    var values = validateRegister(form);
    if (!values) return;
    var submit = form.querySelector('button[type="submit"]');
    submit.disabled = true; submit.textContent = 'Creating account…';
    post('/auth/register', { full_name: values.full_name, email: values.email, phone: values.phone, password: values.password }).then(function() {
      formMessage(form, 'Account created. Taking you to sign in…', true);
      setTimeout(function() { location.href = '/login.html'; }, 700);
    }).catch(function(error) {
      formMessage(form, error.message);
      submit.disabled = false; submit.textContent = 'Create account';
    });
  });
}

// Boot
var pageInitializers = { home: initHome, login: initLogin, register: initRegister, restaurants: initRestaurants, restaurant: initRestaurant, foods: initFoods, food: initFood, cart: initCart, checkout: initCheckout, orders: initOrders, order: initOrder, profile: initProfile, 'restaurant-dashboard': initRestaurantDashboard, 'delivery-dashboard': initDeliveryDashboard, 'admin-dashboard': initAdminDashboard };
(function boot() { renderFooter(); setupPasswordToggles(); loadUser().then(function(user) { renderHeader(user); var initializer = pageInitializers[document.body.dataset.page]; if (initializer) initializer(); }).catch(function(error) { var main = document.querySelector('main'); if (main) main.insertAdjacentHTML('beforeend', failure(error)); }); })();
