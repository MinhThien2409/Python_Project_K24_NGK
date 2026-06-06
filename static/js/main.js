// ==========================================
// GIẢ LẬP DỮ LIỆU SẢN PHẨM & GIỎ HÀNG BAN ĐẦU
// ==========================================
let categories = [
  { slug: 'electronics', name: 'Điện tử' }, 
  { slug: 'food', name: 'Thực phẩm' }, 
  { slug: 'fashion', name: 'Thời trang' }, 
  { slug: 'home', name: 'Nhà cửa' }
];

let products = [
  { id: 1, name: 'Điện thoại thông minh Samsung Galaxy S26', category: 'electronics', price: 19900000, emoji: '📱', shop: 'Samsung Official', sold: 45 },
  { id: 2, name: 'Tai nghe chụp tai chống ồn Sony WH-1000XM5', category: 'electronics', price: 6500000, emoji: '🎧', shop: 'Sony Store', sold: 28 },
  { id: 3, name: 'Combo Rau củ quả hữu cơ xanh sạch 3kg', category: 'food', price: 120000, emoji: '🥦', shop: 'Nông trại Đà Lạt', sold: 154 }
];

let cart = [];
let currentUser = null;
let orders = [];
let sellers = [];

// ==========================================
// 1. CHUYỂN ĐỔI VIEW & ĐIỀU HƯỚNG
// ==========================================
function switchViewMode(mode) {
  // Bật tắt 3 khối giao diện chính
  document.getElementById('userInterface').style.display = (mode === 'user') ? 'block' : 'none';
  document.getElementById('adminInterface').style.display = (mode === 'admin') ? 'block' : 'none';
  document.getElementById('sellerDashboard').style.display = (mode === 'seller') ? 'block' : 'none';

  // Đổi màu nút Active trên thanh chuyển đổi
  document.querySelectorAll('.view-switcher button').forEach(btn => btn.classList.remove('active'));

  if (mode === 'user') {
      const btn = document.getElementById('btnViewUser');
      if (btn) btn.classList.add('active');
  }
  else if (mode === 'admin') {
      const btn = document.getElementById('btnViewAdmin');
      if (btn) btn.classList.add('active');
      initAdminDashboard(); // Tải dữ liệu tổng quan cho Admin
  }
  else if (mode === 'seller') {
      const btn = document.getElementById('btnViewSeller');
      if (btn) btn.classList.add('active');
      switchSellerTab('overview'); // Mở tab mặc định của Seller
  }
}
function switchSellerTab(tabName) {
  // Tắt hết trạng thái active của menu bên trái
  document.querySelectorAll('#sellerDashboard .admin-menu-item').forEach(el => el.classList.remove('active'));
  // Ẩn hết các nội dung (pane) bên phải
  document.querySelectorAll('#sellerDashboard .admin-pane').forEach(el => el.style.display = 'none');

  // Bật menu và nội dung tương ứng
  const menuItem = document.getElementById(`smenu-${tabName}`);
  if (menuItem) menuItem.classList.add('active');

  const paneItem = document.getElementById(`spane-${tabName}`);
  if (paneItem) paneItem.style.display = 'block';

  // Nơi đây sau này chúng ta sẽ gọi API tương ứng
  if (tabName === 'overview') {
      document.getElementById('sellerOverviewContent').innerHTML = `
          <div style="padding: 20px; text-align: center; color: var(--text-muted);">
              Đang tải dữ liệu tổng quan gian hàng...
          </div>`;
      // Ví dụ: fetch('/api/seller/overview')
  } else if (tabName === 'products') {
      // fetch('/api/seller/products')
  } else if (tabName === 'orders') {
      // fetch('/api/seller/orders')
  }
}

function switchAdminTab(tabName) {
  document.querySelectorAll('.admin-menu-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.admin-pane').forEach(el => el.style.display = 'none');

  document.getElementById(`menu-${tabName}`).classList.add('active');
  document.getElementById(`pane-${tabName}`).style.display = 'block';

  if(tabName === 'dashboard') initAdminDashboard();
  if(tabName === 'products') renderAdminProducts();
  if(tabName === 'categories') renderAdminCategories();
  if(tabName === 'permissions') {
      renderPermissionsTable();
      setTimeout(() => {
          loadUsersToDropdown();
      }, 100);
  }

    if (tabName === 'sellers') renderAdminSellers();
}

// ==========================================
// 2. API: ĐĂNG NHẬP, ĐĂNG KÝ & QUẢN LÝ TÀI KHOẢN
// ==========================================
function switchAuthForm(form) {
  document.getElementById('tabLogin').classList.toggle('active', form === 'login');
  document.getElementById('tabRegister').classList.toggle('active', form === 'register');
  document.getElementById('formLogin').classList.toggle('active', form === 'login');
  document.getElementById('formRegister').classList.toggle('active', form === 'register');
}

function openAuthModal() { document.getElementById('authModal').classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

// HÀM XỬ LÝ ĐĂNG NHẬP
// Thay thế toàn bộ hàm handleLogin cũ bằng hàm này
async function handleLogin(e) {
  e.preventDefault();
  const tendangnhap = document.getElementById('loginUsername').value.trim();
  const mat_khau = document.getElementById('loginPass').value;

  try {
    const response = await fetch('http://localhost:5000/api/dang-nhap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tendangnhap, mat_khau })
    });

    const result = await response.json();
    console.log("Backend trả về:", result);

    if (result.status === true) {
      currentUser = result.data;

      closeModal('authModal');
      showToast(`🎉 ${result.message}`);
      updateHeaderForUser();

      const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;
      if (maQuyen === 20) {
        switchViewMode('admin');
        loadAndApplyAdminPermissions(currentUser.ma_user);
      } else {
        switchViewMode('user'); // Seller và Customer đều ở trang user
      }

    } else {
      // ✅ Thêm else này — hiện lỗi khi sai tài khoản/mật khẩu
      showToast('❌ ' + result.message);
    }

  } catch (error) {
    console.error(error);
    showToast('❌ Lỗi kết nối máy chủ!');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const ten_user = document.getElementById('regName').value.trim();
  const tendangnhap = document.getElementById('regUsername').value.trim(); // ID mới
  const sdt = document.getElementById('regPhone').value.trim();
  const mat_khau = document.getElementById('regPass').value;

  try {
    const response = await fetch('http://localhost:5000/api/dang-ky', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ten_user, tendangnhap, sdt, mat_khau })
    });
    // ... code xử lý kết quả giữ nguyên ...
  } catch (error) { showToast('❌ Lỗi kết nối!'); }
}
// HÀM MỞ BẢNG THÔNG TIN CÁ NHÂN (Cho phép chỉnh sửa)
function openProfileModal() {
  if(!currentUser) return;

  let ten_user = currentUser.ten_user || currentUser.FullName || "";
  let sdt = currentUser.sdt || currentUser.Phone || "";
  let dia_chi = currentUser.dia_chi || currentUser.Address || "";
  let cmnd = currentUser.cmnd || currentUser.NationalId || "";
  let ma_nhom_quyen = currentUser.ma_nhom_quyen || currentUser.Role_id;

  let role = "Khách hàng";
  if (ma_nhom_quyen === 20) role = "Quản trị viên (Admin)";
  else if (ma_nhom_quyen === 13) role = "Đối tác Bán hàng";
  else if (ma_nhom_quyen === 5) role = "Nhân viên Kế toán";
  else if (currentUser.ten_nhom_quyen) role = currentUser.ten_nhom_quyen;

  document.getElementById('profileInfoRows').innerHTML = `
    <div style="margin-bottom: 12px;">👑 <b>Vai trò:</b> <span class="badge-status status-confirmed">${role}</span></div>

    <div class="form-group">
      <label>Họ và tên</label>
      <input type="text" id="editName" value="${ten_user}" placeholder="Nhập họ tên...">
    </div>
    <div class="form-group">
      <label>Số điện thoại</label>
      <input type="tel" id="editPhone" value="${sdt === 'Chưa có SĐT' ? '' : sdt}" placeholder="Nhập SĐT...">
    </div>
    <div class="form-group">
      <label>Địa chỉ giao hàng</label>
      <input type="text" id="editAddress" value="${dia_chi === 'Chưa có địa chỉ' ? '' : dia_chi}" placeholder="Nhập địa chỉ...">
    </div>
    <div class="form-group">
      <label>Số CMND/CCCD</label>
      <input type="text" id="editCmnd" value="${cmnd === 'Chưa cập nhật CMND' ? '' : cmnd}" placeholder="Nhập số CMND/CCCD...">
    </div>

    <button class="btn-submit" style="background: var(--green); width: 100%; margin-top: 10px;" onclick="updateUserProfile()">💾 Lưu cập nhật thông tin</button>
  `;

  if(ma_nhom_quyen !== 14 && ma_nhom_quyen !== 15) {
     document.getElementById('btnGoAdminFromProfile').style.display = 'block';
  } else {
     document.getElementById('btnGoAdminFromProfile').style.display = 'none';
  }

  document.getElementById('profileModal').classList.add('show');
}

// GỬI DỮ LIỆU CẬP NHẬT LÊN SERVER
async function updateUserProfile() {
  const newName = document.getElementById('editName').value.trim();
  const newPhone = document.getElementById('editPhone').value.trim();
  const newAddress = document.getElementById('editAddress').value.trim();
  const newCmnd = document.getElementById('editCmnd').value.trim();

  if(!newName) { showToast("⚠️ Họ tên không được để trống!"); return; }

  try {
    const response = await fetch('http://localhost:5000/api/cap-nhat-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ma_user: currentUser.ma_user || currentUser.UserId,
        ten_user: newName,
        sdt: newPhone,
        dia_chi: newAddress,
        cmnd: newCmnd
      })
    });

    const result = await response.json();
    if(result.status == true) {
      showToast('✅ ' + result.message);
      currentUser.ten_user = newName;
      currentUser.sdt = newPhone;
      currentUser.dia_chi = newAddress;
      currentUser.cmnd = newCmnd;
      document.getElementById('topbarUserText').innerHTML = `🟢 Xin chào: <b>${newName}</b>`;
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối đến máy chủ Backend!');
  }
}

function goToAdmin() {
  closeModal('profileModal');
  switchViewMode('admin');
}

function goToUser() {
  closeModal('profileModal');
  switchViewMode('user');
}

// CẬP NHẬT HÀM ĐĂNG XUẤT
function handleLogout() {
  currentUser = null;

  // Reset topbar & nút header
  document.getElementById('topbarUserText').textContent  = '👤 Chưa đăng nhập';
  document.getElementById('authBtnLabel').textContent    = 'Đăng nhập';
  document.getElementById('hdrAuthBtn').style.display = 'flex';
document.getElementById('hdrUserBtn').style.display = 'none';
  document.getElementById('hdrAuthBtn').style.display    = 'flex';
  document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
  document.getElementById('hdrGoSellerBtn').style.display = 'none';

  // Ẩn các nút chỉ hiện khi đã đăng nhập
  ['hdrProfileBtn', 'hdrHistoryBtn', 'hdrNotifBtn', 'hdrWishBtn', 'hdrSellerBtn'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });

  closeModal('profileModal');
  switchViewMode('user');
  cart = [];
  updateCartBadge();
  showToast('Đã đăng xuất thành công.');
}

// ==========================================
// 3. API: DỮ LIỆU USER & QUẢN LÝ PHÂN QUYỀN
// ==========================================
async function loadUsersToDropdown() {
  const selectBox = document.getElementById('permUserSelect');
  if (!selectBox) return; 

  try {
    const response = await fetch('http://localhost:5000/api/users');
    const result = await response.json();

    if(result.status === true && Array.isArray(result.data)) {
      selectBox.innerHTML = '<option value="">-- Chọn tài khoản --</option>';
      result.data.forEach(u => {
        let id = u.ma_user || u.UserId;
        let name = u.ten_user || u.FullName;
        let role = u.ten_nhom_quyen || u.RoleName || "Chưa cấp quyền";

        let opt = document.createElement('option');
        opt.value = id;
        opt.textContent = `${name} - [${role}]`;
        selectBox.appendChild(opt);
      });
    }
  } catch(e) {
    showToast("❌ Không thể tải danh sách tài khoản!");
  }
}



const sysModules = [
  { id: 1, name: 'Quản lý Sản phẩm' }, { id: 2, name: 'Quản lý Đơn hàng' },
  { id: 3, name: 'Quản lý Người dùng' }, { id: 4, name: 'Quản lý Danh mục' },
  { id: 5, name: 'Quản lý Cấu hình hệ thống' }, { id: 6, name: 'Quản lý Đối tác kinh doanh' }
];

async function loadAndApplyAdminPermissions(ma_user) {
  try {
    const res = await fetch(`http://localhost:5000/api/quyen-cua-user/${ma_user}`);
    const result = await res.json();
    if(result.status === true) {
      const menuMap = { 1: 'menu-products', 2: 'menu-orders', 3: 'menu-permissions', 4: 'menu-categories', 6: 'menu-sellers' };
      Object.values(menuMap).forEach(menuId => { const el = document.getElementById(menuId); if(el) el.style.display = 'none'; });
      result.data.forEach(quyen => {
        if(quyen.xem === true && menuMap[quyen.ma_chuc_nang]) {
           const el = document.getElementById(menuMap[quyen.ma_chuc_nang]);
           if(el) el.style.display = 'block';
        }
      });
    }
  } catch(e) { console.error("Lỗi tải menu phân quyền:", e); }
}

async function loadUserPermissions() {
  const ma_user = document.getElementById('permUserSelect').value;
  if(!ma_user) {
      showToast("⚠️ Vui lòng chọn một tài khoản từ danh sách để xem quyền!");
      return;
  }

  try {
    const res = await fetch(`http://localhost:5000/api/quyen-cua-user/${ma_user}`);
    const result = await res.json();

    if(result.status === true) {
      toggleAllPermissions(false);
      result.data.forEach(q => {
         let cbView = document.querySelector(`.cb-view[data-mod="${q.ma_chuc_nang}"]`);
         let cbAdd = document.querySelector(`.cb-add[data-mod="${q.ma_chuc_nang}"]`);
         let cbEdit = document.querySelector(`.cb-edit[data-mod="${q.ma_chuc_nang}"]`);
         let cbDelete = document.querySelector(`.cb-delete[data-mod="${q.ma_chuc_nang}"]`);

         if(cbView) cbView.checked = q.xem;
         if(cbAdd) cbAdd.checked = q.them;
         if(cbEdit) cbEdit.checked = q.sua;
         if(cbDelete) cbDelete.checked = q.xoa;
      });
      showToast('✅ Đã tải cấu hình quyền hiện tại của tài khoản từ Database!');
    } else {
      showToast('❌ ' + result.message);
    }
  } catch(e) {
      showToast("❌ Không thể kết nối tới Server để lấy quyền!");
  }
}
// Thay thế toàn bộ hàm handleSaveProfile cũ bằng hàm này
async function handleSaveProfile(e) {
  e.preventDefault();
  const newPass = document.getElementById('profileNewPass').value;
  const confirmPass = document.getElementById('profileConfirmPass').value;

  if (newPass && newPass !== confirmPass) { showToast('⚠️ Mật khẩu xác nhận không khớp!'); return; }

  const newName = document.getElementById('profileName').value;
  const newPhone = document.getElementById('profilePhone').value;
  const newAddress = document.getElementById('profileAddress').value;
  const newNationalId = document.getElementById('profileNationalId').value;

  try {
    const response = await fetch('http://localhost:5000/api/cap-nhat-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ma_user: currentUser.id,
        ten_user: newName,
        sdt: newPhone,
        dia_chi: newAddress,
        cmnd: newNationalId
      })
    });

    const result = await response.json();
    if(result.status === true) {
      // Cập nhật biến JS cục bộ
      currentUser.name = newName;
      currentUser.phone = newPhone;
      currentUser.address = newAddress;
      currentUser.nationalId = newNationalId;

      updateHeaderForUser();
      closeModalById('profileModal');
      showToast('✅ Cập nhật thông tin thành công!');
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (error) {
    showToast('❌ Lỗi kết nối đến máy chủ!');
  }
}
function updateHeaderForUser() {
  if (!currentUser) return;

  // Cập nhật tên và các nút cơ bản
  document.getElementById('topbarUserText').innerHTML = `🟢 <b>${currentUser.ten_user || currentUser.FullName}</b>`;
  document.getElementById('authBtnLabel').textContent = 'Tài khoản';

  // Ẩn nút Đăng nhập, hiện nút User
  document.getElementById('hdrAuthBtn').style.display = 'none';
  document.getElementById('hdrUserBtn').style.display = 'flex';
  document.getElementById('userBtnLabel').textContent = currentUser.ten_user || currentUser.FullName;
  document.getElementById('hdrUserBtn').onclick = openProfileModal;

  // Hiện các nút chức năng mặc định
  document.getElementById('hdrProfileBtn').style.display = 'flex';
  document.getElementById('hdrHistoryBtn').style.display = 'flex';
  document.getElementById('hdrNotifBtn').style.display = 'flex';
  document.getElementById('hdrWishBtn').style.display = 'flex';

  // --- LOGIC PHÂN QUYỀN HIỂN THỊ NÚT SELLER ---
  const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;

  if (maQuyen === 20 || currentUser.role === 'Admin') {
      // 1. Nếu là Admin -> Hiện thanh Admin màu đen trên cùng
      document.getElementById('viewSwitcher').style.display = 'flex';
      document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
      document.getElementById('hdrGoSellerBtn').style.display = 'none';
  }
  else if (maQuyen === 13 || currentUser.role === 'Seller') {
      // 2. Nếu là Seller -> BẬT NÚT KÊNH NGƯỜI BÁN
      document.getElementById('viewSwitcher').style.display = 'none';
      document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
      document.getElementById('hdrGoSellerBtn').style.display = 'flex';
  }
  else {
      // 3. Nếu là Khách hàng thường -> BẬT NÚT ĐĂNG KÝ BÁN
      document.getElementById('viewSwitcher').style.display = 'none';
      document.getElementById('hdrGoSellerBtn').style.display = 'none';
      document.getElementById('hdrRegisterSellerBtn').style.display = 'flex';
  }
}
async function savePermissions() {
  const ma_user = document.getElementById('permUserSelect').value;
  if(!ma_user) { showToast("⚠️ Vui lòng chọn một tài khoản trước khi lưu!"); return; }

  let permissionsData = [];
  sysModules.forEach(m => {
    permissionsData.push({
      ma_chuc_nang: m.id,
      xem: document.querySelector(`.cb-view[data-mod="${m.id}"]`)?.checked || false,
      them: document.querySelector(`.cb-add[data-mod="${m.id}"]`)?.checked || false,
      sua: document.querySelector(`.cb-edit[data-mod="${m.id}"]`)?.checked || false,
      xoa: document.querySelector(`.cb-delete[data-mod="${m.id}"]`)?.checked || false
    });
  });

  try {
    const response = await fetch('http://localhost:5000/api/cap-quyen-ngoai-le', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ma_user: ma_user, permissions: permissionsData })
    });
    const result = await response.json();
    showToast((result.status ? '💾 ' : '❌ ') + result.message);
  } catch(e) { showToast("❌ Lỗi kết nối lưu phân quyền!"); }
}

function renderPermissionsTable() {
  const tbody = document.getElementById('tblPermissionsBody');
  const searchTxt = document.getElementById('searchModule')?.value.toLowerCase() || '';
  const filteredModules = sysModules.filter(m => m.name.toLowerCase().includes(searchTxt));
  if(document.getElementById('moduleCountText')) document.getElementById('moduleCountText').textContent = `${filteredModules.length} chức năng`;

  tbody.innerHTML = filteredModules.map(m => `
    <tr style="border-bottom: 1px solid var(--border);">
      <td style="border-right: 1px solid var(--border); font-weight: 500;">${m.name}</td>
      <td style="text-align: center;"><input type="checkbox" style="transform: scale(1.3); cursor: pointer;" class="cb-view" data-mod="${m.id}"></td>
      <td style="text-align: center;"><input type="checkbox" style="transform: scale(1.3); cursor: pointer;" class="cb-add" data-mod="${m.id}"></td>
      <td style="text-align: center;"><input type="checkbox" style="transform: scale(1.3); cursor: pointer;" class="cb-edit" data-mod="${m.id}"></td>
      <td style="text-align: center;"><input type="checkbox" style="transform: scale(1.3); cursor: pointer;" class="cb-delete" data-mod="${m.id}"></td>
    </tr>
  `).join('');
}

function toggleAllPermissions(status) {
  document.querySelectorAll('#tblPermissionsBody input[type="checkbox"]').forEach(cb => cb.checked = status);
  showToast(status ? '✅ Đã chọn Cấp tất cả quyền!' : '❌ Đã Thu hồi tất cả quyền!');
}
if(document.getElementById('searchModule')) {
    document.getElementById('searchModule').addEventListener('input', renderPermissionsTable);
}

// ==========================================
// 4. CÁC HÀM XỬ LÝ GIAO DIỆN (UI) KHÁC
// ==========================================
function updateCartBadge() { document.getElementById('cartBadge').textContent = cart.reduce((a, c) => a + c.qty, 0); }

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(t._timeoutId);
  t._timeoutId = setTimeout(() => t.classList.remove('show'), 2500);
}

function initAdminDashboard() {
  document.getElementById('statRevenue').textContent = '240.000đ';
  document.getElementById('statOrders').textContent = '1';
  document.getElementById('statProducts').textContent = products.length;
}

function applyUserFilters() {
  let filtered = [...products]; // products đã là data từ API sau loadProducts()

  // Lọc theo danh mục checkbox
  const checkedCats = [...document.querySelectorAll('#filterCatList input:checked')]
    .map(cb => cb.value);
  if (checkedCats.length > 0) {
    filtered = filtered.filter(p => checkedCats.includes(p.category_name));
  }

  // Lọc theo search text
  const searchText = document.getElementById('userSearchInput')?.value.toLowerCase() || '';
  if (searchText) {
    filtered = filtered.filter(p => p.name.toLowerCase().includes(searchText));
  }

  // Lọc theo giá
  const priceMin = Number(document.getElementById('priceMin')?.value) || 0;
  const priceMax = Number(document.getElementById('priceMax')?.value) || Infinity;
  if (priceMin || priceMax !== Infinity) {
    filtered = filtered.filter(p => p.price >= priceMin && p.price <= priceMax);
  }

  // Lọc theo danh mục dropdown header
  const catSelect = document.getElementById('searchCategorySelect')?.value;
  if (catSelect && catSelect !== 'all') {
    filtered = filtered.filter(p => p.category_name === catSelect);
  }

  // Sắp xếp
  const sort = document.getElementById('sortSelect')?.value || 'default';
  if (sort === 'price-asc')  filtered.sort((a, b) => a.price - b.price);
  if (sort === 'price-desc') filtered.sort((a, b) => b.price - a.price);
  if (sort === 'rating')     filtered.sort((a, b) => (b.rating||0) - (a.rating||0));
  if (sort === 'bestseller') filtered.sort((a, b) => (b.sold||0) - (a.sold||0));

  renderUserProducts(filtered);
}
function addToCart(productId) {
  if (!currentUser) {
    showToast('⚠️ Vui lòng đăng nhập để mua hàng!');
    openAuthModal();
    return;
  }

  const product = products.find(p => p.id === productId);
  if (!product) return;

  const existing = cart.find(c => c.id === productId);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }

  updateCartBadge();
  showToast(`✅ Đã thêm "${product.name}" vào giỏ hàng!`);
}

async function loadProducts() {
  try {
    const res    = await fetch('http://localhost:5000/api/products');
    const result = await res.json();
    if (result.status) {
      products = result.data; // Cập nhật biến global
      renderUserProducts(products);
    }
  } catch (e) {
    console.error('Lỗi load sản phẩm:', e);
  }
}

// Cuối file - thay renderUserProducts(products) bằng:
loadCategories();
loadProducts();  // ← Thay dòng này
async function handleSellerRegister(e) {
  e.preventDefault();
  if (!currentUser) { showToast('⚠️ Vui lòng đăng nhập trước!'); return; }

  const body = {
    UserId     : currentUser.ma_user,
    StoreName  : document.getElementById('selShopName').value.trim(),
    Phone      : document.getElementById('selPhone').value.trim(),
    Category   : document.getElementById('selCat').value,
    Description: document.getElementById('sellerDesc').value.trim(),
    NationalId : document.getElementById('sellerNationalId').value.trim()
  };

  try {
    const res    = await fetch('http://localhost:5000/api/dang-ky-gian-hang', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(body)
    });
    const result = await res.json();
    showToast(result.status ? '🎉 ' + result.message : '❌ ' + result.message);
    if (result.status) closeModal('sellerModal');
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
let currentPermType = 'user'; // Mặc định là phân quyền theo user

function switchPermType(type) {
    currentPermType = type;
    const btnUser = document.getElementById('btnRoleTypeUser');
    const btnGroup = document.getElementById('btnRoleTypeGroup');
    const label = document.getElementById('permLabel');

    if (type === 'user') {
        // Đổi UI sang chế độ User
        btnUser.style.background = 'var(--primary)'; btnUser.style.color = 'white';
        btnGroup.style.background = 'white'; btnGroup.style.color = 'var(--text)';
        label.textContent = 'Tài khoản cần phân quyền:';
        loadUsersToDropdown(); // Gọi hàm cũ của bạn
    } else {
        // Đổi UI sang chế độ Group
        btnGroup.style.background = 'var(--primary)'; btnGroup.style.color = 'white';
        btnUser.style.background = 'white'; btnUser.style.color = 'var(--text)';
        label.textContent = 'Nhóm quyền cần cấu hình:';
        loadRolesToDropdown(); // Hàm mới (xem bên dưới)
    }

    document.querySelectorAll('#tblPermissionsBody input[type="checkbox"]')
        .forEach(cb => cb.checked = false);
}

// Hàm load danh sách các nhóm quyền (Hardcode hoặc lấy từ API)
function loadRolesToDropdown() {
    const selectBox = document.getElementById('permUserSelect');
    if (!selectBox) return;

    // Vì nhóm quyền ít khi thay đổi, bạn có thể cấu hình cứng ở đây cho nhanh
    selectBox.innerHTML = `
    <option value="">-- Chọn nhóm quyền --</option>
    <option value="20">🛠️ Quản trị viên (Admin)</option>
    <option value="13">🏪 Đối tác Bán hàng (Seller)</option>
    <option value="5">💰 Nhân viên Kế toán</option>
    <option value="14">👤 Khách hàng mặc định</option>
    `;
}
async function apDungQuyenNhomChoUser() {
    // Chỉ hoạt động khi đang ở chế độ phân quyền cá nhân
    if (currentPermType !== 'user') {
        showToast("⚠️ Chức năng này chỉ dùng khi phân quyền theo Cá nhân!");
        return;
    }

    const ma_user = document.getElementById('permUserSelect').value;
    if (!ma_user) {
        showToast("⚠️ Vui lòng chọn tài khoản trước!");
        return;
    }

    // Xác nhận trước khi thực hiện
    if (!confirm("Thao tác này sẽ XÓA mọi quyền ngoại lệ và đặt lại về quyền mặc định của nhóm. Tiếp tục?")) return;

    try {
        const res = await fetch('http://localhost:5000/api/ap-dung-quyen-nhom-cho-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ma_user: ma_user })
        });
        const result = await res.json();

        showToast((result.status ? '✅ ' : '❌ ') + result.message);

        // Tự động tải lại quyền mới để hiển thị lên bảng
        if (result.status) loadPermissionsData();

    } catch(e) {
        showToast("❌ Lỗi kết nối server!");
    }
}
async function loadPermissionsData() {
    const targetId = document.getElementById('permUserSelect').value;
    if (!targetId) {
        showToast("⚠️ Vui lòng chọn đối tượng để xem quyền!");
        return;
    }

    // Nếu là user thì gọi API user, nếu là group thì gọi API group
    const apiUrl = currentPermType === 'user'
        ? `http://localhost:5000/api/quyen-cua-user/${targetId}`
        : `http://localhost:5000/api/quyen-cua-nhom/${targetId}`;

    try {
        const res = await fetch(apiUrl);
        const result = await res.json();

        if (result.status === true) {
            toggleAllPermissions(false);
            // ... Logic tick checkbox giống hệt hàm cũ của bạn
            result.data.forEach(q => {
               let cbView = document.querySelector(`.cb-view[data-mod="${q.ma_chuc_nang}"]`);
               let cbAdd = document.querySelector(`.cb-add[data-mod="${q.ma_chuc_nang}"]`);
               let cbEdit = document.querySelector(`.cb-edit[data-mod="${q.ma_chuc_nang}"]`);
               let cbDelete = document.querySelector(`.cb-delete[data-mod="${q.ma_chuc_nang}"]`);

               if(cbView) cbView.checked = q.xem;
               if(cbAdd) cbAdd.checked = q.them;
               if(cbEdit) cbEdit.checked = q.sua;
               if(cbDelete) cbDelete.checked = q.xoa;
            });
            showToast('✅ Đã tải cấu hình phân quyền!');
        } else {
            showToast('❌ ' + result.message);
        }
    } catch(e) {
        showToast("❌ Lỗi kết nối Server!");
    }
}

async function savePermissionsData() {
    const targetId = document.getElementById('permUserSelect').value;
    if (!targetId) { showToast("⚠️ Vui lòng chọn đối tượng trước khi lưu!"); return; }

    let permissionsData = [];
    sysModules.forEach(m => {
        permissionsData.push({
            ma_chuc_nang: m.id,
            xem: document.querySelector(`.cb-view[data-mod="${m.id}"]`)?.checked || false,
            them: document.querySelector(`.cb-add[data-mod="${m.id}"]`)?.checked || false,
            sua: document.querySelector(`.cb-edit[data-mod="${m.id}"]`)?.checked || false,
            xoa: document.querySelector(`.cb-delete[data-mod="${m.id}"]`)?.checked || false
        });
    });

    const apiUrl = currentPermType === 'user'
        ? 'http://localhost:5000/api/cap-quyen-ngoai-le'  // API lưu cho user
        : 'http://localhost:5000/api/cap-quyen-nhom';    // API lưu cho nhóm (role)

    const payload = currentPermType === 'user'
        ? { ma_user: targetId, permissions: permissionsData }
        : { role_id: targetId, permissions: permissionsData };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        showToast((result.status ? '💾 ' : '❌ ') + result.message);
    } catch(e) { showToast("❌ Lỗi kết nối lưu phân quyền!"); }
}
// Thêm hàm render bảng Sellers trong admin (tab sellers)
async function renderAdminSellers() {
  try {
    const res    = await fetch('http://localhost:5000/api/seller-requests');
    const result = await res.json();
    const tbody  = document.getElementById('tblAdminSellersBody');

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Chưa có yêu cầu nào</td></tr>`;
      return;
    }

    tbody.innerHTML = result.data.map(r => `
      <tr>
        <td><b>${r.shop_name}</b></td>
        <td>${r.ten_user}</td>
        <td>${r.phone}</td>
        <td>${r.category}</td>
        <td style="max-width:160px; font-size:12px; color:var(--text-secondary);">${r.description || '—'}</td>
        <td>
          ${r.status === 'pending'  ? '<span class="badge-status status-pending">Chờ duyệt</span>'   : ''}
          ${r.status === 'approved' ? '<span class="badge-status status-confirmed">Đã duyệt</span>'  : ''}
          ${r.status === 'rejected' ? '<span class="badge-status status-cancelled">Từ chối</span>'   : ''}
        </td>
        <td>
          ${r.status === 'pending' ? `
            <button class="admin-action-btn btn-confirm" onclick="duyetSeller(${r.request_id})">✅ Duyệt</button>
            <button class="admin-action-btn btn-cancel"  onclick="tuChoiSeller(${r.request_id})">❌ Từ chối</button>
          ` : '—'}
        </td>
      </tr>
    `).join('');

    // Cập nhật badge số đơn chờ
    const pending = result.data.filter(r => r.status === 'pending').length;
    document.getElementById('sellerPendingBadge').textContent = pending ? `(${pending})` : '';

  } catch (e) {
    showToast('❌ Không thể tải danh sách yêu cầu người bán!');
  }
}

async function duyetSeller(request_id) {
  if (!confirm('Xác nhận duyệt yêu cầu này? Tài khoản sẽ được cấp quyền Seller.')) return;
  try {
    const res    = await fetch(`http://localhost:5000/api/duyet-seller/${request_id}`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ reviewed_by: currentUser?.ma_user })
    });
    const result = await res.json();
    showToast(result.status ? '✅ ' + result.message : '❌ ' + result.message);
    if (result.status) renderAdminSellers(); // Reload bảng
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function tuChoiSeller(request_id) {
  const ly_do = prompt('Lý do từ chối (tuỳ chọn):') ?? '';
  try {
    const res    = await fetch(`http://localhost:5000/api/tu-choi-seller/${request_id}`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ reviewed_by: currentUser?.ma_user, ly_do })
    });
    const result = await res.json();
    showToast(result.status ? '✅ ' + result.message : '❌ ' + result.message);
    if (result.status) renderAdminSellers();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
// Load danh mục từ API đổ vào tất cả dropdowns
async function loadCategories() {
  try {
    const res    = await fetch('http://localhost:5000/api/categories');
    const result = await res.json();
    if (!result.status || !result.data.length) return;

    const options = result.data.map(c =>
      `<option value="${c.name}">${c.name}</option>`
    ).join('');

    // Đổ vào dropdown đăng ký gian hàng
    const selCat = document.getElementById('selCat');
    if (selCat) selCat.innerHTML = options;

    // Đổ vào dropdown thêm sản phẩm (admin)
    const prodCat = document.getElementById('prodCategory');
    if (prodCat) prodCat.innerHTML = options;

    // Đổ vào thanh tìm kiếm header
    const searchCat = document.getElementById('searchCategorySelect');
    if (searchCat) {
      searchCat.innerHTML = `<option value="all">Tất cả danh mục</option>` + options;
    }

    // Đổ vào sidebar filter
    const filterCatList = document.getElementById('filterCatList');
    if (filterCatList) {
      filterCatList.innerHTML = result.data.map(c => `
        <label class="filter-option">
          <input type="checkbox" value="${c.name}" onchange="applyUserFilters()"> ${c.name}
        </label>
      `).join('');
    }

  } catch (e) {
    console.error('Lỗi load categories:', e);
  }
}
function renderUserProducts(arr) {
  const container = document.getElementById('userProductsGrid');
  if (!container) return;

  if (!arr || arr.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <div class="icon">📦</div>
        <p>Không có sản phẩm nào</p>
      </div>`;
    return;
  }

  container.innerHTML = arr.map(p => `
    <div class="product-card" onclick="openProductDetail(${p.id})">
      <div class="card-img">${p.emoji || '📦'}</div>
      <div class="card-body">
        <div class="card-title">${p.name}</div>
        ${p.old_price ? `<div style="font-size:12px; color:var(--text-muted); text-decoration:line-through;">${Number(p.old_price).toLocaleString('vi-VN')}đ</div>` : ''}
        <div class="card-price">${Number(p.price).toLocaleString('vi-VN')}đ</div>
        <div class="card-footer">
          <span style="font-size:11px; color:var(--text-muted);">⭐ ${p.rating || 4.5} · Đã bán ${p.sold || 0}</span>
          <button class="add-cart-btn" onclick="event.stopPropagation(); addToCart(${p.id})">+ Giỏ hàng</button>
        </div>
      </div>
    </div>`).join('');
}

// Hàm mở modal đăng ký gian hàng - load categories trước
function openSellerRegisterModal() {
  if (!currentUser) {
    showToast('⚠️ Vui lòng đăng nhập trước khi đăng ký bán hàng!');
    openAuthModal();
    return;
  }
  loadCategories(); // ← Load dữ liệu trước khi hiện modal
  document.getElementById('sellerModal').classList.add('show');
}

// KHỞI CHẠY GIAO DIỆN MẶC ĐỊNH
loadCategories();
loadProducts();