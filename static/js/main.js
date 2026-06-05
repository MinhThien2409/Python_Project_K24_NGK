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
  document.getElementById('userInterface').style.display = (mode === 'user') ? 'block' : 'none';
  document.getElementById('adminInterface').style.display = (mode === 'admin') ? 'block' : 'none';

  if(mode === 'admin') initAdminDashboard();
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

      // Cập nhật tên hiển thị trên topbar
      document.getElementById('topbarUserText').innerHTML =
        `🟢 Xin chào: <b>${currentUser.ten_user}</b>`;
      document.getElementById('authBtnLabel').textContent = currentUser.ten_user;

      document.getElementById('hdrAuthBtn').style.display = 'none';
      document.getElementById('hdrUserBtn').style.display = 'flex';
      document.getElementById('userBtnLabel').textContent = currentUser.ten_user;

      // Hiện các nút cần đăng nhập
      document.getElementById('hdrProfileBtn').style.display = 'flex';
      document.getElementById('hdrHistoryBtn').style.display = 'flex';
      document.getElementById('hdrNotifBtn').style.display  = 'flex';
      document.getElementById('hdrWishBtn').style.display   = 'flex';

      closeModal('authModal'); // ✅ Đúng tên hàm

      showToast(`🎉 ${result.message}`);

      // Điều hướng theo quyền
      if (currentUser.ma_nhom_quyen === 20) {
        switchViewMode('admin');
      } else {
        switchViewMode('user');
      }

    } else {
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

function applyUserFilters() { renderUserProducts(products); }

function renderUserProducts(arr) {
  const container = document.getElementById('userProductsGrid');
  if(!container) return;
  container.innerHTML = arr.map(p => `
    <div class="product-card">
      <div class="card-img">${p.emoji}</div>
      <div class="card-body">
        <div class="card-title">${p.name}</div>
        <div class="card-price">${p.price.toLocaleString('vi-VN')}đ</div>
      </div>
    </div>`).join('');
}

// KHỞI CHẠY GIAO DIỆN MẶC ĐỊNH
renderUserProducts(products);