// ==========================================
// GIẢ LẬP DỮ LIỆU SẢN PHẨM & GIỎ HÀNG BAN ĐẦU
// ==========================================
let categories = [
  { slug: 'electronics', name: 'Điện tử' }, 
  { slug: 'food', name: 'Thực phẩm' }, 
  { slug: 'fashion', name: 'Thời trang' }, 
  { slug: 'home', name: 'Nhà cửa' }
];
let currentPage = 1;
const ITEMS_PER_PAGE = 12;
let currentFilteredProducts = []; // lưu lại mảng đang hiển thị để dùng khi đổi trang

let products = [
  { id: 1, name: 'Điện thoại thông minh Samsung Galaxy S26', category: 'electronics', price: 19900000, emoji: '📱', shop: 'Samsung Official', sold: 45 },
  { id: 2, name: 'Tai nghe chụp tai chống ồn Sony WH-1000XM5', category: 'electronics', price: 6500000, emoji: '🎧', shop: 'Sony Store', sold: 28 },
  { id: 3, name: 'Combo Rau củ quả hữu cơ xanh sạch 3kg', category: 'food', price: 120000, emoji: '🥦', shop: 'Nông trại Đà Lạt', sold: 154 }
];
const SELLER_CITY = 'hcm'; // mặc định HCM

let currentShippingFee = 25000; // biến global lưu phí ship hiện tại

let cart = [];
let currentUser = null;
let orders = [];
let sellers = [];
// ==========================================
// GIỮ ĐĂNG NHẬP SAU KHI F5 (REFRESH TRANG)
// ==========================================

function luuDangNhap(user) {
  localStorage.setItem('pobby_user', JSON.stringify(user));
}

function xoaDangNhap() {
  localStorage.removeItem('pobby_user');
}

async function khoiPhucDangNhap() {
  const saved = localStorage.getItem('pobby_user');
  if (!saved) return;

  try {
    currentUser = JSON.parse(saved);

    // ✅ Hỏi server phiên hiện tại (FR-009): hợp lệ + trạng thái tài khoản
    const res    = await fetch('/api/phien');
    const result = await res.json();
    if (!result.status || (result.data && result.data.trang_thai === 'banned')) {
      showToast('🔒 ' + (result.message || 'Phiên đăng nhập đã hết hạn!'));
      xoaDangNhap();
      sessionStorage.removeItem('pobby_redirect');
      currentUser = null;
      return;
    }

    // ✅ Vai trò LẤY TỪ SERVER (012 FR-007: không tin dữ liệu role trong localStorage)
    if (result.data) currentUser = { ...currentUser, ...result.data };
    luuDangNhap(currentUser);

    // ✅ Đọc + xóa đích điều hướng tạm sau reload (012 FR-004); không có thì mặc định
    const dichDieuHuong = sessionStorage.getItem('pobby_redirect');
    sessionStorage.removeItem('pobby_redirect');

    updateHeaderForUser();
    await loadCartFromServer();

    if ((currentUser.ma_nhom_quyen || currentUser.Role_id) === 3) {
      await loadSellerStore();
    }
    hienThiGiaoDienTheoVaiTro(dichDieuHuong);

  } catch (e) {
    console.error('Lỗi khôi phục đăng nhập:', e);
    xoaDangNhap();
    sessionStorage.removeItem('pobby_redirect');
    currentUser = null;
  }
}

// ==========================================
// 1. CHUYỂN ĐỔI VIEW & ĐIỀU HƯỚNG
// ==========================================
// Hiển thị giao diện theo vai trò (009 US1). Tham số `dich` ∈ {admin, seller, user}
// để ép đích sau đăng nhập/reload (012 US1/US3); không truyền → suy ra từ vai trò.
function hienThiGiaoDienTheoVaiTro(dich) {
  const maQuyen = currentUser ? (currentUser.ma_nhom_quyen || currentUser.Role_id) : 4;
  const laQuanTri = (maQuyen === 1 || maQuyen === 2);
  const laSeller  = (maQuyen === 3);

  // Suy đích mặc định từ vai trò khi không được ép đích
  if (!dich) {
    if (laQuanTri) dich = 'admin';
    else if (laSeller && currentUser && currentUser.store) dich = 'seller';
    else dich = 'user';
  }
  // An toàn: đích 'seller' chỉ hợp lệ với Seller thật sự
  if (dich === 'seller' && !laSeller) dich = 'user';

  document.getElementById('userInterface').style.display   = (dich === 'user')   ? 'block' : 'none';
  document.getElementById('adminInterface').style.display  = (dich === 'admin')  ? 'block' : 'none';
  document.getElementById('sellerDashboard').style.display = (dich === 'seller') ? 'block' : 'none';

  if (dich === 'seller') {
    switchSellerTab('overview');
  } else if (dich === 'admin') {
    renderAdminMenuTheoVaiTro();
  }
}

// Menu khu quản trị theo vai trò (009 US2/US3): Admin 2 mục, Quản lý 3 mục
function renderAdminMenuTheoVaiTro() {
  const maQuyen = currentUser ? (currentUser.ma_nhom_quyen || currentUser.Role_id) : 4;
  const laAdmin = maQuyen === 1 || currentUser?.role === 'Admin';
  const laQuanLy = maQuyen === 2 || currentUser?.role === 'Quản lý';

  const menu = {
    categories: laQuanLy,          // Quản lý: Quản lý danh mục
    sellers:    laQuanLy,          // Quản lý: Duyệt người bán hàng
    users:      laQuanLy || laAdmin, // cả hai: Danh sách tài khoản (015 FR-005 gộp bảng)
  };
  for (const [tab, hien] of Object.entries(menu)) {
    const el = document.getElementById(`menu-${tab}`);
    if (el) el.style.display = hien ? 'block' : 'none';
  }

  // Chọn pane mặc định theo vai trò (không mở tab đã bị cắt)
  const tabMacDinh = laAdmin ? 'users' : (laQuanLy ? 'categories' : null);
  if (tabMacDinh) {
    switchAdminTab(tabMacDinh);
  }
}

// Seller mở Kênh Người Bán (thay cho switchViewMode('seller'))
function showSellerDashboard() {
  if (!currentUser) return;
  const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;
  if (maQuyen !== 3 && currentUser.role !== 'Seller') {
    showToast('🚫 Bạn không có quyền truy cập kênh người bán!');
    return;
  }
  document.getElementById('userInterface').style.display   = 'none';
  document.getElementById('adminInterface').style.display  = 'none';
  document.getElementById('sellerDashboard').style.display = 'block';
  switchSellerTab('overview');
}

async function switchSellerTab(tabName) {
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
    await renderSellerOverview();
  } else if (tabName === 'products') {
    await renderSellerProducts();
  } else if (tabName === 'nhaphang') {
    await renderSellerNhapHang();
  } else if (tabName === 'orders') {
    await renderSellerOrders();
  } else if (tabName === 'shop') {
    await renderTrangShop();
  } else if (tabName === 'gia') {
    await renderGiaBan();
  }
}

async function renderSellerOrders() {
  const storeId = currentUser?.store?.store_id;
  const tbody   = document.getElementById('tblSellerOrdersBody');

  if (!storeId) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">
      Không tìm thấy gian hàng!
    </td></tr>`;
    return;
  }

  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">
    ⏳ Đang tải...
  </td></tr>`;

  try {
    const res    = await fetch(`/api/don-hang/cua-seller/${storeId}`);
    const result = await res.json();

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">
        Chưa có đơn hàng nào cho gian hàng này
      </td></tr>`;
      return;
    }

    const statusMap = {
      'Pending'  : { label: 'Chờ duyệt',   cls: 'status-pending'   },
      'Confirmed': { label: 'Đã xác nhận', cls: 'status-confirmed' },
      'Shipping' : { label: 'Đang giao',   cls: 'status-shipping'  },
      'Completed': { label: 'Hoàn thành',  cls: 'status-done'      },
      'Cancelled': { label: 'Đã hủy',      cls: 'status-cancelled' },
    };

    tbody.innerHTML = result.data.map(o => {
      const s = statusMap[o.Status] || { label: o.Status, cls: '' };
      const itemSummary = (o.Items || [])
        .map(i => `${i.Emoji || '📦'} ${i.ProductName} x${i.Quantity}`)
        .join('<br>');
      const createdAt = o.CreatedAt
        ? new Date(o.CreatedAt).toLocaleDateString('vi-VN', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
          })
        : '—';

      // Nút thao tác theo từng trạng thái
      let actionBtn = `<span style="font-size:12px; color:var(--text-muted);">—</span>`;

      if (o.Status === 'Pending') {
        actionBtn = `
          <button class="admin-action-btn btn-confirm"
            onclick="sellerCapNhatDon(${o.OrderId}, 'Confirmed')">
            ✅ Xác nhận
          </button>`;
      } else if (o.Status === 'Confirmed') {
        actionBtn = `
          <button class="admin-action-btn btn-confirm"
            onclick="sellerCapNhatDon(${o.OrderId}, 'Shipping')">
            🚚 Giao hàng
          </button>`;
      } else if (o.Status === 'Shipping') {
        actionBtn = `
          <button class="admin-action-btn btn-confirm"
            onclick="sellerCapNhatDon(${o.OrderId}, 'Completed')">
            🏁 Hoàn thành
          </button>`;
      }

      return `
        <tr>
          <td style="font-weight:700; color:var(--text-muted);">#${o.OrderId}</td>
          <td>
            <div style="font-weight:600;">${o.ReceiverName}</div>
            <div style="font-size:11px; color:var(--text-muted);">📞 ${o.ReceiverPhone}</div>
            <div style="font-size:11px; color:var(--text-muted);">👤 ${o.CustomerName || '—'}</div>
          </td>
          <td style="font-size:12px; max-width:180px;">${itemSummary || '—'}</td>
          <td style="font-weight:700; color:var(--red);">
            ${Number(o.TotalAmount).toLocaleString('vi-VN')}đ
            <div style="font-size:11px; color:var(--text-muted); font-weight:400;">
              Ship: ${Number(o.ShippingFee || 0).toLocaleString('vi-VN')}đ
            </div>
          </td>
          <td><span class="badge-status ${s.cls}">${s.label}</span></td>
          <td style="font-size:12px; color:var(--text-muted);">${createdAt}</td>
          <td>${actionBtn}</td>
        </tr>
      `;
    }).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--red);">
      ❌ Lỗi tải dữ liệu
    </td></tr>`;
    console.error('Lỗi renderSellerOrders:', e);
  }
}

// Hàm xử lý cập nhật trạng thái từ phía Seller
async function sellerCapNhatDon(orderId, newStatus) {
  const labelMap = {
    'Confirmed': 'Xác nhận đơn hàng',
    'Shipping' : 'Chuyển sang Đang giao',
    'Completed': 'Hoàn thành đơn hàng',
  };
  const label = labelMap[newStatus] || newStatus;
  if (!confirm(`${label} cho đơn #${orderId}?`)) return;

  try {
    const res    = await fetch(`/api/don-hang/${orderId}/trang-thai`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ status: newStatus })
    });
    const result = await res.json();

    if (result.status) {
      showToast(`✅ ${result.message}`);
      await renderSellerOrders(); // Reload lại bảng
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
async function renderSellerOverview() {
  const container = document.getElementById('sellerOverviewContent');
  const store = currentUser?.store;

  if (!store) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="icon">🏪</div>
        <p>Không tìm thấy thông tin gian hàng!</p>
      </div>`;
    return;
  }

  container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted);">Đang tải...</div>`;

  try {
    // Lấy sản phẩm của store
    const res    = await fetch(`/api/products/store/${store.store_id}`);
    const result = await res.json();
    const prods  = result.status ? result.data : [];

    // Tính toán số liệu từ dữ liệu sản phẩm
    const tongSanPham  = prods.length;
    const sapHetHang   = prods.filter(p => (p.quantity || 0) <= 5).length;
    const tongDoanhThu = prods.reduce((sum, p) => sum + (p.price * (p.sold || 0)), 0);
    const topProducts  = [...prods].sort((a, b) => (b.sold || 0) - (a.sold || 0)).slice(0, 5);

    container.innerHTML = `
      <!-- Thông tin gian hàng -->
      <div class="admin-card" style="display:flex; align-items:center; gap:20px; background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color:white;">
        <div style="width:64px; height:64px; border-radius:14px; background:rgba(255,255,255,0.2);
                    display:flex; align-items:center; justify-content:center; font-size:30px; flex-shrink:0;">
          🏪
        </div>
        <div>
          <div style="font-size:20px; font-weight:800; margin-bottom:4px;">${store.store_name || 'Gian hàng của tôi'}</div>
          <div style="opacity:0.8; font-size:13px;">📍 ${store.address || 'Chưa cập nhật địa chỉ'}</div>
          <div style="margin-top:8px;">
            <span style="background:rgba(255,255,255,0.2); padding:3px 10px; border-radius:99px; font-size:12px; font-weight:700;">
              ✅ Đang hoạt động
            </span>
          </div>
        </div>
      </div>

      <!-- Thống kê nhanh -->
      <div class="stats-grid" style="margin-bottom:24px;">
        <div class="stat-box">
          <div style="font-size:13px; color:var(--text-secondary);">Tổng sản phẩm</div>
          <div class="stat-val">${tongSanPham}</div>
        </div>
        <div class="stat-box">
          <div style="font-size:13px; color:var(--text-secondary);">Sắp hết hàng</div>
          <div class="stat-val" style="color:${sapHetHang > 0 ? 'var(--red)' : 'var(--green)'};">
            ${sapHetHang}
          </div>
        </div>
        <div class="stat-box">
          <div style="font-size:13px; color:var(--text-secondary);">Tổng đã bán</div>
          <div class="stat-val">${prods.reduce((s, p) => s + (p.sold || 0), 0)}</div>
        </div>
        <div class="stat-box">
          <div style="font-size:13px; color:var(--text-secondary);">Doanh thu ước tính</div>
          <div class="stat-val" style="font-size:16px;">
            ${tongDoanhThu.toLocaleString('vi-VN')}đ
          </div>
        </div>
      </div>

      <!-- Sản phẩm bán chạy -->
      <div class="admin-card">
        <h3 style="margin-bottom:14px;">🔥 Sản phẩm bán chạy nhất</h3>

        ${topProducts.length === 0
          ? `<div class="empty-state"><div class="icon">📦</div><p>Chưa có sản phẩm nào</p></div>`
          : topProducts.map((p, i) => `
            <div style="
                display:flex;
                align-items:center;
                gap:12px;
                padding:10px 0;
                border-bottom:1px solid var(--border);
            ">
              
              <div style="
                  width:28px;
                  height:28px;
                  border-radius:50%;
                  background:var(--primary-light);
                  color:var(--primary);
                  display:flex;
                  align-items:center;
                  justify-content:center;
                  font-weight:800;
                  font-size:13px;
                  flex-shrink:0;
              ">
                ${i + 1}
              </div>

              <div style="width:60px;height:60px;flex-shrink:0;">
                ${
                  p.image_url
                    ? `<img src="/static/${p.image_url}"
                          alt="${p.name}"
                          style="
                            width:60px;
                            height:60px;
                            object-fit:cover;
                            border-radius:8px;
                            border:1px solid #ddd;
                          ">`
                    : `<span style="font-size:32px;">${p.emoji || '📦'}</span>`
                }
              </div>

              <div style="flex:1; min-width:0;">
                <div style="
                    font-weight:600;
                    font-size:14px;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                  ${p.name}
                </div>

                <div style="
                    font-size:12px;
                    color:var(--text-secondary);
                ">
                  Đã bán: <b>${p.sold || 0}</b> · Còn: <b>${p.quantity || 0}</b>
                </div>
              </div>

              <div style="
                  font-weight:700;
                  color:var(--red);
                  font-size:14px;
                  flex-shrink:0;
              ">
                ${Number(p.price).toLocaleString('vi-VN')}đ
              </div>

            </div>
          `).join('')
        }
      </div>

      <!-- Cảnh báo hàng sắp hết -->
      ${sapHetHang > 0 ? `
        <div class="admin-card" style="border-left: 4px solid var(--red);">
          <h3 style="color:var(--red); margin-bottom:10px;">⚠️ Cảnh báo tồn kho thấp</h3>
          ${prods.filter(p => (p.quantity || 0) <= 5).map(p => `
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:8px 0; border-bottom:1px solid var(--border); font-size:13px;">
              <span>${p.emoji || '📦'} ${p.name}</span>
              <span style="color:var(--red); font-weight:700;">
                Còn ${p.quantity || 0} sản phẩm
              </span>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;

  } catch (e) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="icon">❌</div>
        <p>Lỗi tải dữ liệu tổng quan!</p>
      </div>`;
    console.error('Lỗi renderSellerOverview:', e);
  }
}
async function renderSellerProducts() {
    const storeId = currentUser?.store?.store_id;
    if (!storeId) {
        document.getElementById('tblSellerProductsBody').innerHTML =
            `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">
                Không tìm thấy gian hàng!
            </td></tr>`;
        return;
    }

    const res    = await fetch(`/api/products/store/${storeId}`);
    const result = await res.json();
    const tbody  = document.getElementById('tblSellerProductsBody');

    if (!result.data.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">
            Chưa có sản phẩm nào. Hãy thêm sản phẩm đầu tiên!
        </td></tr>`;
        return;
    }

    tbody.innerHTML = result.data.map(p => `
        <tr>
            <td style="text-align:center;">
              ${
                p.image_url
                  ? `<img src="/static/${p.image_url}"
                          alt="${p.name}"
                          style="
                            width:60px;
                            height:60px;
                            object-fit:cover;
                            border-radius:8px;
                            border:1px solid #ddd;
                          ">`
                  : `<span style="font-size:28px;">${p.emoji || '📦'}</span>`
              }
            </td>
            <td>
                <div style="font-weight:600;">${p.name}</div>
                <div style="font-size:11px; color:var(--text-muted);">${p.category_name || ''}</div>
            </td>
            <td style="color:var(--red); font-weight:700;">
                ${Number(p.price).toLocaleString('vi-VN')}đ
            </td>
            <td style="text-align:center; color:${p.quantity <= 5 ? 'var(--red)' : 'inherit'}">
                ${p.quantity || 0}
            </td>
            <td style="text-align:center;">${p.sold || 0}</td>
            <td>
                <button class="admin-action-btn btn-edit" 
                    onclick="openEditSellerProduct(${p.id})">✏️ Sửa</button>
            </td>
        </tr>
    `).join('');
}

// Mở modal sửa sản phẩm từ Seller Dashboard
async function openEditSellerProduct(productId) {
  try {
    const res    = await fetch(`/api/products/${productId}`);
    const result = await res.json();

    if (!result.status) { showToast('❌ Không tìm thấy sản phẩm!'); return; }

    const p = result.data;

    document.getElementById('adminProductModalTitle').textContent = '✏️ Chỉnh sửa sản phẩm';
    document.getElementById('editProductId').value               = p.id;
    document.getElementById('editProductId').dataset.sellerMode  = 'true'; // ← đánh dấu Seller mode
    document.getElementById('prodName').value                    = p.name;
    document.getElementById('prodPrice').value                   = p.price;
    document.getElementById('prodOldPrice').value                = p.old_price || '';
    document.getElementById('prodStock').value                   = p.quantity;
    document.getElementById('prodEmoji').value                   = p.emoji || '';
    document.getElementById('prodDesc').value                    = p.description || '';

    await loadCategoriesForProductModal(p.category_name);

    document.getElementById('adminProductModal').classList.add('show');

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
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
    const response = await fetch('/api/dang-nhap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tendangnhap, mat_khau })
    });

    const result = await response.json();
    console.log("Backend trả về:", result);

    if (result.status === true) {
      currentUser = result.data;
      luuDangNhap(currentUser);

      closeModal('authModal');
      showToast(`🎉 ${result.message}`);
      updateHeaderForUser();
      await loadCartFromServer();

      // 012 US1 (FR-001/FR-002): quyết định đích điều hướng theo vai trò rồi reload
      const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;
      let dichDieuHuong = 'user';
      if (maQuyen === 1 || maQuyen === 2) {
        dichDieuHuong = 'admin';               // Admin / Quản lý → khu quản trị
      } else if (maQuyen === 3) {
        await loadSellerStore();               // Seller: có gian hàng → kênh bán; chưa có → mua sắm
        dichDieuHuong = currentUser.store ? 'seller' : 'user';
      }
      sessionStorage.setItem('pobby_redirect', dichDieuHuong);
      console.log('Điều hướng sau đăng nhập:', dichDieuHuong);
      location.reload();
      return;

    } else {
      // ✅ Thêm else này — hiện lỗi khi sai tài khoản/mật khẩu
      showToast('❌ ' + result.message);
    }

  } catch (error) {
    console.error(error);
    showToast('❌ Lỗi kết nối máy chủ!');
  }
}
async function loadSellerStore() {
  try {
    const res    = await fetch(`/api/stores/by-user/${currentUser.ma_user}`);
    const result = await res.json();

    if (result.status) {
      currentUser.store = result.data;
      console.log("Store của Seller:", currentUser.store);
    } else {
      // Có quyền Seller nhưng chưa có Store → thông báo
      currentUser.store = null;
      showToast('⚠️ Tài khoản chưa có gian hàng, vui lòng liên hệ Admin!');
    }
  } catch (e) {
    console.error("Lỗi load store:", e);
    currentUser.store = null;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const ten_user    = document.getElementById('regName').value.trim();
  const tendangnhap = document.getElementById('regUsername').value.trim();
  const sdt         = document.getElementById('regPhone').value.trim();
  const mat_khau    = document.getElementById('regPass').value;

  // Validate cơ bản
  if (!ten_user || !tendangnhap || !mat_khau) {
    showToast('⚠️ Vui lòng điền đầy đủ thông tin bắt buộc!');
    return;
  }

  try {
    const response = await fetch('/api/dang-ky', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ten_user, tendangnhap, sdt, mat_khau })
    });

    const result = await response.json();

    if (result.status === true) {
      showToast('🎉 ' + (result.message || 'Đăng ký thành công! Vui lòng đăng nhập.'));

      // Reset form đăng ký
      document.getElementById('formRegister').reset();

      // Chuyển sang tab đăng nhập, điền sẵn tên đăng nhập vừa tạo
      switchAuthForm('login');
      document.getElementById('loginUsername').value = tendangnhap;
      document.getElementById('loginPass').value = '';

    } else {
      showToast('❌ ' + (result.message || 'Đăng ký thất bại!'));
    }

  } catch (error) {
    console.error(error);
    showToast('❌ Lỗi kết nối máy chủ!');
  }
}
// HÀM MỞ BẢNG THÔNG TIN CÁ NHÂN (Cho phép chỉnh sửa)
// HÀM MỞ BẢNG THÔNG TIN CÁ NHÂN (Cho phép chỉnh sửa)
async function openProfileModal() {
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

  // Kiểm tra xem user có ít nhất 1 quyền "xem" hay không
  // → quyết định hiện/ẩn nút "Vào khu vực Quản trị hệ thống"
  await checkAdminAccessButton(ma_nhom_quyen);

  document.getElementById('profileModal').classList.add('show');
}

// Kiểm tra quyền truy cập khu vực Admin dựa trên vai trò chuẩn (Admin=1, Quản lý=2)
function checkAdminAccessButton(ma_nhom_quyen) {
  const btn = document.getElementById('btnGoAdminFromProfile');
  if (!btn) return;

  const laQuanTri = ma_nhom_quyen === 1 || ma_nhom_quyen === 2;
  btn.style.display = laQuanTri ? 'block' : 'none';
}

// Admin/Quản lý có toàn quyền truy cập các phân hệ quản trị
function hasPermission(tabName, action = 'xem') {
  return true;
}

function switchAdminTab(tabName) {
  // Kiểm tra quyền XEM trước khi cho vào
  if (!hasPermission(tabName, 'xem')) {
    showToast(`🚫 Bạn không có quyền xem mục này!`);
    return;
  }

  // Tắt tất cả menu active
  document.querySelectorAll('#adminInterface .admin-menu-item')
    .forEach(el => el.classList.remove('active'));

  // Ẩn tất cả pane
  document.querySelectorAll('#adminInterface .admin-pane')
    .forEach(el => el.style.display = 'none');

  // Bật menu đang chọn
  const menuEl = document.getElementById(`menu-${tabName}`);
  if (menuEl) menuEl.classList.add('active');

  // Hiện pane đang chọn
  const paneEl = document.getElementById(`pane-${tabName}`);
  if (paneEl) paneEl.style.display = 'block';

  // Gọi hàm load dữ liệu tương ứng (009: bỏ các tab đã cắt)
  if (tabName === 'categories')  renderAdminCategories();
  if (tabName === 'sellers')     renderAdminSellers();
  if (tabName === 'users') {
  renderUserRoleFilter();
  renderAdminUsers();
}
}

// GỬI DỮ LIỆU CẬP NHẬT LÊN SERVER
async function updateUserProfile() {
  const newName = document.getElementById('editName').value.trim();
  const newPhone = document.getElementById('editPhone').value.trim();
  const newAddress = document.getElementById('editAddress').value.trim();
  const newCmnd = document.getElementById('editCmnd').value.trim();

  if(!newName) { showToast("⚠️ Họ tên không được để trống!"); return; }

  try {
    const response = await fetch('/api/cap-nhat-profile', {
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

// ── 005 US5: tab hồ sơ + submit profile/password qua server ──
function switchProfileTab(tab) {
  for (const t of ['info', 'edit', 'security']) {
    document.getElementById(`ptab-${t}`)?.classList.toggle('active', t === tab);
    document.getElementById(`pcontent-${t}`)?.classList.toggle('active', t === tab);
  }
  if (tab === 'edit' && currentUser) {
    const ten = document.getElementById('profTen');
    if (ten && !ten.value) {
      ten.value = currentUser.ten_user || '';
      document.getElementById('profDiaChi').value = currentUser.dia_chi || '';
      document.getElementById('profSdt').value = currentUser.sdt || '';
    }
  }
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const ten = document.getElementById('profTen').value.trim();
  const diaChi = document.getElementById('profDiaChi').value.trim();
  const sdt = document.getElementById('profSdt').value.trim();
  if (!ten) { showToast('⚠️ Họ tên không được để trống!'); return; }
  try {
    const res = await fetch('/api/cap-nhat-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ten_user: ten, dia_chi: diaChi, sdt })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + result.message);
    if (result.status) {
      currentUser.ten_user = ten;
      currentUser.dia_chi = diaChi;
      currentUser.sdt = sdt;
      switchProfileTab('info');
      openProfileModal();
    }
  } catch (err) {
    showToast('❌ Lỗi kết nối đến máy chủ Backend!');
  }
}

async function handleChangePassword(e) {
  e.preventDefault();
  const cu = document.getElementById('pwCu').value;
  const moi = document.getElementById('pwMoi').value;
  try {
    const res = await fetch('/api/doi-mat-khau', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mat_khau_cu: cu, mat_khau_moi: moi })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + result.message);
    if (result.status) {
      document.getElementById('pwCu').value = '';
      document.getElementById('pwMoi').value = '';
      switchProfileTab('info');
    }
  } catch (err) {
    showToast('❌ Lỗi kết nối đến máy chủ Backend!');
  }
}

function goToUser() {
  closeModal('profileModal');
  hienThiGiaoDienTheoVaiTro();
}

// CẬP NHẬT HÀM ĐĂNG XUẤT (012 US2: reload về trang mua sắm chưa đăng nhập)
async function handleLogout() {
  // Xóa phiên phía server trước (fail-safe: lỗi mạng vẫn xóa local khi reload)
  try {
    await fetch('/api/dang-xuat', { method: 'POST' });
  } catch (e) {
    console.error('Lỗi đăng xuất phía server:', e);
  }

  // Xóa sạch dữ liệu phiên cũ ở client
  currentUser = null;
  cart = [];
  xoaDangNhap();
  sessionStorage.removeItem('pobby_redirect');
  closeModal('profileModal');

  // Reload để giao diện tải lại ở trạng thái chưa đăng nhập (FR-003)
  location.reload();
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
    const response = await fetch('/api/cap-nhat-profile', {
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

  // Hiện các nút chức năng mặc định — profile cũ đã gỡ (017 US4)
  document.getElementById('hdrHistoryBtn').style.display = 'flex';


  // --- PHÂN BIỆT HIỂN THỊ THEO VAI TRÒ CHUẨN (1=Admin, 2=Quản lý, 3=Seller, 4=Customer) ---
  const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;
  const tenVaiTro = currentUser.ten_vai_tro || currentUser.ten_vai_tro_hien_thi;
  const laAdmin = tenVaiTro === 'Admin' || maQuyen === 1;

  // Tab Quản lý tài khoản đã gộp vào menu-users (015 FR-005) — không còn menu-quanly

  if (maQuyen === 1 || maQuyen === 2 || currentUser.role === 'Admin') {
      // 1. Admin/Quản lý -> đã chuyển sang khu quản trị, không hiện nút đăng ký bán
      document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
      document.getElementById('hdrGoSellerBtn').style.display = 'none';
  }
  else if (maQuyen === 3 || currentUser.role === 'Seller') {
      // 2. Seller -> BẬT NÚT KÊNH NGƯỜI BÁN
      document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
      document.getElementById('hdrGoSellerBtn').style.display = 'flex';
  }
  else {
      // 3. Khách hàng thường -> BẬT NÚT ĐĂNG KÝ BÁN
      document.getElementById('hdrGoSellerBtn').style.display = 'none';
      document.getElementById('hdrRegisterSellerBtn').style.display = 'flex';
  }
}

// ==========================================
// 4. CÁC HÀM XỬ LÝ GIAO DIỆN (UI) KHÁC
// ==========================================
function updateCartBadge() {
  const tong = cart.reduce((s, c) => s + (Number(c.Quantity) || Number(c.qty) || 0), 0);
  document.getElementById('cartBadge').textContent = Math.max(0, Math.floor(tong)) || 0;
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(t._timeoutId);
  t._timeoutId = setTimeout(() => t.classList.remove('show'), 2500);
}

async function initAdminDashboard() {
  try {
    const res    = await fetch('/api/thong-ke/tong-quan');
    const result = await res.json();
    if (!result.status) return;

    const d = result.data;

    // ── Stat boxes ──────────────────────────────────────────
    document.getElementById('statRevenue').textContent =
      Number(d.doanh_thu).toLocaleString('vi-VN') + 'đ';
    document.getElementById('statOrders').textContent  = d.tong_don;
    document.getElementById('statProducts').textContent = d.tong_san_pham;
    document.getElementById('statPending').textContent  = d.cho_duyet;

    // ── Top sản phẩm bán chạy ───────────────────────────────
    const maxSold = Math.max(...d.top_san_pham.map(p => p.sold), 1);
    document.getElementById('bestSellersChart').innerHTML =
      d.top_san_pham.map((p, i) => `
        <div style="display:flex; align-items:center; gap:12px; padding:8px 0;
                    border-bottom:1px solid var(--border);">
          <div style="width:24px; height:24px; border-radius:50%;
                      background:var(--primary-light); color:var(--primary);
                      display:flex; align-items:center; justify-content:center;
                      font-weight:800; font-size:12px; flex-shrink:0;">
            ${i + 1}
          </div>
          <div style="width:40px;height:40px;flex-shrink:0;">
            ${
              p.image_url
                ? `<img src="/static/${p.image_url}"
                      alt="${p.name}"
                      style="
                        width:40px;
                        height:40px;
                        object-fit:cover;
                        border-radius:8px;
                        border:1px solid #ddd;
                      ">`
                : `<span style="font-size:22px;">${p.emoji || '📦'}</span>`
            }
          </div>
          <div style="flex:1; min-width:0;">
            <div style="font-weight:600; font-size:13px; white-space:nowrap;
                        overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
            <div style="margin-top:4px; background:var(--bg); border-radius:4px;
                        height:6px; overflow:hidden;">
              <div style="height:100%; background:var(--primary); border-radius:4px;
                          width:${Math.round(p.sold / maxSold * 100)}%;
                          transition: width 0.6s ease;"></div>
            </div>
          </div>
          <div style="text-align:right; flex-shrink:0;">
            <div style="font-weight:700; color:var(--primary);">
              ${p.sold} đã bán
            </div>
            <div style="font-size:11px; color:var(--text-muted);">
              ${Number(p.price).toLocaleString('vi-VN')}đ
            </div>
          </div>
        </div>
      `).join('') || '<div style="color:var(--text-muted); text-align:center;">Chưa có dữ liệu</div>';

    // ── Đơn hàng gần đây ────────────────────────────────────
    const statusMap = {
      'Pending'  : { label: 'Chờ duyệt',   cls: 'status-pending'   },
      'Confirmed': { label: 'Đã xác nhận', cls: 'status-confirmed' },
      'Shipping' : { label: 'Đang giao',   cls: 'status-shipping'  },
      'Completed': { label: 'Hoàn thành',  cls: 'status-done'      },
      'Cancelled': { label: 'Đã hủy',      cls: 'status-cancelled' },
    };

    document.getElementById('tblRecentOrders').innerHTML =
      d.don_gan_day.map(o => {
        const s = statusMap[o.status] || { label: o.status, cls: '' };
        const date = new Date(o.created_at)
          .toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit', year:'numeric' });
        return `
          <tr>
            <td style="padding:8px; border-bottom:1px solid var(--border);
                       font-weight:700; color:var(--text-muted);">#${o.order_id}</td>
            <td style="padding:8px; border-bottom:1px solid var(--border);">
              <div style="font-weight:600;">${o.receiver_name}</div>
              <div style="font-size:11px; color:var(--text-muted);">${o.customer_name}</div>
            </td>
            <td style="padding:8px; border-bottom:1px solid var(--border);
                       font-weight:700; color:var(--red);">
              ${Number(o.total_amount).toLocaleString('vi-VN')}đ
            </td>
            <td style="padding:8px; border-bottom:1px solid var(--border);">
              <span class="badge-status ${s.cls}">${s.label}</span>
            </td>
            <td style="padding:8px; border-bottom:1px solid var(--border);
                       font-size:12px; color:var(--text-muted);">${date}</td>
          </tr>
        `;
      }).join('') ||
      `<tr><td colspan="5" style="text-align:center; padding:20px;
             color:var(--text-muted);">Chưa có đơn hàng nào</td></tr>`;

    // ── Biểu đồ doanh thu theo tháng ────────────────────────
    await renderRevenueChart();

  } catch (e) {
    console.error('Lỗi load dashboard:', e);
  }
}

async function renderRevenueChart() {
  const res    = await fetch('/api/thong-ke/doanh-thu-theo-thang?year=2026');
  const result = await res.json();
  if (!result.status) return;

  const data   = result.data;
  const maxRev = Math.max(...data.map(d => d.doanh_thu), 1);
  const months = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12'];

  // Thêm chart container vào dashboard nếu chưa có
  let chartEl = document.getElementById('revenueChartWrap');
  if (!chartEl) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    card.innerHTML = `
      <h3 style="margin-bottom:16px;">📊 Doanh thu theo tháng (2026)</h3>
      <div id="revenueChartWrap"
           style="display:flex; align-items:flex-end; gap:8px;
                  height:160px; padding-bottom:24px; position:relative;">
      </div>`;
    document.getElementById('pane-dashboard').appendChild(card);
    chartEl = document.getElementById('revenueChartWrap');
  }

  chartEl.innerHTML = data.map((d, i) => {
    const pct    = maxRev > 0 ? Math.round(d.doanh_thu / maxRev * 100) : 0;
    const hasRev = d.doanh_thu > 0;
    return `
      <div style="flex:1; display:flex; flex-direction:column;
                  align-items:center; gap:4px; height:100%; justify-content:flex-end;">
        ${hasRev ? `
          <div style="font-size:9px; color:var(--text-muted); font-weight:600;">
            ${Math.round(d.doanh_thu/1000000)}tr
          </div>` : ''}
        <div style="width:100%; background:${hasRev ? 'var(--primary)' : 'var(--border)'};
                    border-radius:4px 4px 0 0; height:${Math.max(pct, 3)}%;
                    transition: height 0.5s ease; cursor:pointer;"
             title="${months[i]}: ${Number(d.doanh_thu).toLocaleString('vi-VN')}đ (${d.so_don} đơn)">
        </div>
        <div style="font-size:10px; color:var(--text-muted); font-weight:600;
                    position:absolute; bottom:0;">${months[i]}</div>
      </div>
    `;
  }).join('');
}
function applyUserFilters() {
  currentPage=1
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
  // Thay đoạn lọc theo giá cũ bằng đoạn này
const priceMin = Number(document.getElementById('priceMin')?.dataset.rawValue) || 0;
const priceMax = Number(document.getElementById('priceMax')?.dataset.rawValue) || Infinity;
if (priceMin > 0 || priceMax !== Infinity) {
  filtered = filtered.filter(p => p.price >= priceMin && (priceMax === Infinity || p.price <= priceMax));
}

  // Lọc theo danh mục dropdown header
  const catSelect = document.getElementById('searchCategorySelect')?.value;
  if (catSelect && catSelect !== 'all') {
    filtered = filtered.filter(p => p.category_name === catSelect);
  }
   const chkInStock = document.getElementById('chkInStock')?.checked;
  if (chkInStock) {
    filtered = filtered.filter(p => (p.quantity || 0) > 0);
  }

  // ✅ Lọc: Đang giảm giá
  const chkOnSale = document.getElementById('chkOnSale')?.checked;
  if (chkOnSale) {
    filtered = filtered.filter(p => p.old_price && Number(p.old_price) > Number(p.price));
  }


  // Sắp xếp
  const sort = document.getElementById('sortSelect')?.value || 'default';
  if (sort === 'price-asc')  filtered.sort((a, b) => a.price - b.price);
  if (sort === 'price-desc') filtered.sort((a, b) => b.price - a.price);
  if (sort === 'bestseller') filtered.sort((a, b) => (b.sold||0) - (a.sold||0));

  renderUserProducts(filtered);
}

async function loadProducts() {
  try {
    const res    = await fetch('/api/products');
    const result = await res.json();
    if (result.status) {
      products = result.data; // Cập nhật biến global
      renderUserProducts(products);
    }
  } catch (e) {
    console.error('Lỗi load sản phẩm:', e);
  }
}

// ── 005 US1: tìm kiếm server-side (q + category_id) + empty-state ──
async function timKiemSanPhamServer() {
  const input = document.getElementById('userSearchInput');
  const tuKhoa = (input?.value || '').trim();
  const catSelect = document.getElementById('searchCategorySelect')?.value;
  const params = new URLSearchParams();
  if (tuKhoa) params.set('q', tuKhoa);
  if (catSelect && catSelect !== 'all' && !isNaN(Number(catSelect))) {
    params.set('category_id', catSelect);
  }
  try {
    const res = await fetch(`/api/products?${params.toString()}`);
    const result = await res.json();
    if (result.status) {
      products = result.data;
      currentPage = 1;
      renderUserProducts(products);
    } else {
      renderUserProducts([]);
    }
  } catch (e) {
    console.error('Lỗi tìm kiếm sản phẩm:', e);
    applyUserFilters();
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
    Description: document.getElementById('sellerDesc').value.trim()
    // ✅ Không cần gửi NationalId — backend tự lấy từ hồ sơ user
  };

  try {
    const res    = await fetch('/api/dang-ky-gian-hang', {
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




// Thêm hàm render bảng Sellers trong admin (tab sellers)
async function renderAdminSellers() {
  try {
    const res    = await fetch('/api/seller-requests');
    const result = await res.json();

    if (!result.status) {
      showToast('❌ ' + (result.message || 'Không thể tải danh sách yêu cầu người bán!'));
      return;
    }
    const tbody  = document.getElementById('tblAdminSellersBody');

    if (!result.data || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">Chưa có yêu cầu nào</td></tr>`;
      return;
    }

    // 013: bộ lọc trạng thái — đọc dropdown, loc client trước khi vẽ bảng
    const locStatus = document.getElementById('sellerReqFilterStatus')?.value || 'all';
    let listLoc = result.data;
    if (locStatus !== 'all') listLoc = listLoc.filter(r => r.status === locStatus);

    if (!listLoc.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">Không tìm thấy kết quả</td></tr>`;
      return;
    }

    tbody.innerHTML = listLoc.map(r => `
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
        <td style="max-width:160px; font-size:12px; color:var(--text-secondary);">
          ${r.status === 'rejected' ? (r.reject_reason || '—') : '—'}
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
    const res = await fetch(`/api/duyet-seller/${request_id}`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({}) // ReviewedBy lấy từ session phía server
    });
    const result = await res.json();
    showToast(result.status ? '✅ ' + result.message : '❌ ' + result.message);
    renderAdminSellers(); // Reload bảng
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function tuChoiSeller(request_id) {
  const ly_do = prompt('Lý do từ chối (bắt buộc):') ?? '';
  try {
    const res = await fetch(`/api/tu-choi-seller/${request_id}`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ ly_do }) // ReviewedBy lấy từ session phía server
    });
    const result = await res.json();
    showToast(result.status ? '✅ ' + result.message : '❌ ' + result.message);
    renderAdminSellers();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
// Load danh mục từ API đổ vào tất cả dropdowns
async function loadCategories() {
  try {
    const res    = await fetch('/api/categories');
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

  currentFilteredProducts = arr || [];

  if (!arr || arr.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <div class="icon">📦</div>
        <p>Không tìm thấy sản phẩm</p>
      </div>`;
    document.getElementById('paginationWrap').innerHTML = '';
    return;
  }

  // Đảm bảo currentPage hợp lệ
  const totalPages = Math.ceil(arr.length / ITEMS_PER_PAGE);
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  // Cắt mảng theo trang hiện tại
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const pageItems = arr.slice(startIdx, startIdx + ITEMS_PER_PAGE);

  container.innerHTML = pageItems.map(p => `
    <div class="product-card" onclick="openProductDetail(${p.id})">
      <div class="card-img">
        ${
          p.image_url
            ? `<img src="/static/${p.image_url}"
                    alt="${p.name}"
                    style="width:100%;height:100%;object-fit:cover;">`
            : (p.emoji || '📦')
        }
      </div>
      <div class="card-body">
        <div class="card-title">${p.name}</div>
        <div style="font-size:12px; color:var(--text-muted); margin:2px 0 6px;
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                    display:flex; align-items:center; gap:4px;">
          🏪 ${p.shop || 'Pobby Official'}
        </div>
        ${p.old_price ? `<div style="font-size:12px; color:var(--text-muted); text-decoration:line-through;">${Number(p.old_price).toLocaleString('vi-VN')}đ</div>` : ''}
        <div class="card-price">${Number(p.price).toLocaleString('vi-VN')}đ</div>
        <div class="card-footer">
          <span style="font-size:11px; color:var(--text-muted);">Đã bán ${p.sold || 0}</span>
          <button class="add-cart-btn" onclick="event.stopPropagation(); addToCart(${p.id}, 1, ${p.price})">+ Giỏ hàng</button>
        </div>
      </div>
    </div>`).join('');

  renderPagination(arr.length);
}
function renderPagination(totalItems) {
  const wrap = document.getElementById('paginationWrap');
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

  if (totalPages <= 1) {
    wrap.innerHTML = '';
    return;
  }

  let html = '';

  // Nút "Trước"
  html += `<button onclick="goToPage(${currentPage - 1})"
    ${currentPage === 1 ? 'disabled' : ''}
    style="padding:6px 12px; border:1px solid var(--border); border-radius:6px;
           background:white; cursor:${currentPage === 1 ? 'default' : 'pointer'};
           opacity:${currentPage === 1 ? '0.4' : '1'}; font-family:inherit;">‹</button>`;

  // Các nút số trang
  for (let i = 1; i <= totalPages; i++) {
    const active = i === currentPage;
    html += `<button onclick="goToPage(${i})"
      style="padding:6px 12px; border:1px solid var(--border); border-radius:6px;
             background:${active ? 'var(--primary)' : 'white'};
             color:${active ? 'white' : 'var(--text)'};
             font-weight:${active ? '700' : '400'};
             cursor:pointer; font-family:inherit;">${i}</button>`;
  }

  // Nút "Sau"
  html += `<button onclick="goToPage(${currentPage + 1})"
    ${currentPage === totalPages ? 'disabled' : ''}
    style="padding:6px 12px; border:1px solid var(--border); border-radius:6px;
           background:white; cursor:${currentPage === totalPages ? 'default' : 'pointer'};
           opacity:${currentPage === totalPages ? '0.4' : '1'}; font-family:inherit;">›</button>`;

  wrap.innerHTML = html;
}

function goToPage(page) {
  const totalPages = Math.ceil(currentFilteredProducts.length / ITEMS_PER_PAGE);
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  renderUserProducts(currentFilteredProducts);

  // Cuộn lên đầu khu vực sản phẩm cho dễ nhìn
  document.getElementById('userProductsGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Hàm mở modal đăng ký gian hàng - load categories trước
function openSellerRegisterModal() {
  if (!currentUser) {
    showToast('⚠️ Vui lòng đăng nhập trước khi đăng ký bán hàng!');
    openAuthModal();
    return;
  }

  // Kiểm tra nhanh thông tin tài khoản ngay từ client
  const thieu = [];
  if (!currentUser.ten_user)  thieu.push('Họ tên');
  if (!currentUser.sdt || currentUser.sdt === 'Chưa có SĐT')        thieu.push('Số điện thoại');
  if (!currentUser.dia_chi || currentUser.dia_chi === 'Chưa có địa chỉ')      thieu.push('Địa chỉ');
  if (!currentUser.cmnd || currentUser.cmnd === 'Chưa cập nhật CMND')        thieu.push('CMND/CCCD');

  if (thieu.length > 0) {
    showToast(`⚠️ Vui lòng cập nhật: ${thieu.join(', ')} trước khi đăng ký bán hàng!`);
    openProfileModal(); // Đưa thẳng vào trang cập nhật thông tin
    return;
  }

  loadCategories();
  document.getElementById('sellerModal').classList.add('show');
}
// ==========================================
// QUẢN LÝ SẢN PHẨM (ADMIN) - THÊM VÀO main.js
// ==========================================

// ─── RENDER BẢNG SẢN PHẨM ADMIN ─────────────────────────────────────────────
async function renderAdminProducts() {
  const tbody = document.getElementById('tblAdminProductsBody');
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">Đang tải...</td></tr>`;

  const canAdd    = hasPermission('products', 'them');
  const canEdit   = hasPermission('products', 'sua');
  const showActionCol = canEdit; // 015: bỏ nút Xóa (không tồn tại route DELETE /api/products)

  // Ẩn/hiện nút Thêm
  const btnAdd = document.querySelector('#pane-products .checkout-btn');
  if (btnAdd) btnAdd.style.display = canAdd ? '' : 'none';

  try {
    const res    = await fetch('/api/products');
    const result = await res.json();

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="${showActionCol ? 7 : 6}" style="text-align:center; color:var(--text-muted);">Chưa có sản phẩm nào</td></tr>`;
      return;
    }

    // Ẩn/hiện header cột Thao tác
    const thaoTacHeader = document.querySelector('#pane-products thead tr th:last-child');
    if (thaoTacHeader) thaoTacHeader.style.display = showActionCol ? '' : 'none';

    tbody.innerHTML = result.data.map(p => `
      <tr>
        <td style="text-align:center;">
          ${
            p.image_url
              ? `<img src="/static/${p.image_url}"
                    alt="${p.name}"
                    style="
                        width:50px;
                        height:50px;
                        object-fit:cover;
                        border-radius:8px;
                        border:1px solid #ddd;
                    ">`
              : `<span style="font-size:28px">${p.emoji || '📦'}</span>`
          }
        </td>
        <td>
          <div style="font-weight:600;">${p.name}</div>
          <div style="font-size:11px; color:var(--text-muted);">${p.description || ''}</div>
        </td>
        <td>
          <span class="badge-status status-confirmed" style="font-size:11px;">
            ${p.category_name || '—'}
          </span>
        </td>
        <td>
          <div style="font-weight:700; color:var(--red);">
            ${Number(p.price).toLocaleString('vi-VN')}đ
          </div>
          ${p.old_price
            ? `<div style="font-size:11px; color:var(--text-muted); text-decoration:line-through;">
                 ${Number(p.old_price).toLocaleString('vi-VN')}đ
               </div>`
            : ''}
        </td>
        <td style="text-align:center;">
          <span style="font-weight:600; color:${p.quantity <= 5 ? 'var(--red)' : 'var(--text)'};">
            ${p.quantity || 0}
          </span>
        </td>
        <td style="text-align:center;">${p.sold || 0}</td>

        ${showActionCol ? `
        <td>
          ${canEdit
            ? `<button class="admin-action-btn btn-edit"
                        onclick="openEditProductModal(${p.id})">✏️ Sửa</button>`
            : ''}
        </td>` : ''}
      </tr>
    `).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="${showActionCol ? 7 : 6}" style="text-align:center; color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
    console.error('Lỗi renderAdminProducts:', e);
  }
}

// ─── MỞ MODAL THÊM SẢN PHẨM MỚI ─────────────────────────────────────────────
async function openAddProductModal() {
  // Reset form
  document.getElementById('adminProductModalTitle').textContent = '➕ Thêm sản phẩm mới';
  document.getElementById('editProductId').value = '';
  document.getElementById('prodName').value      = '';
  document.getElementById('prodPrice').value     = '';
  document.getElementById('prodOldPrice').value  = '';
  document.getElementById('prodStock').value     = '';
  document.getElementById('prodEmoji').value     = '';
  document.getElementById('prodShop').value      = '';
  document.getElementById('prodDesc').value      = '';

  // Load categories vào dropdown
  await loadCategoriesForProductModal();

  document.getElementById('adminProductModal').classList.add('show');
}

// ─── MỞ MODAL SỬA SẢN PHẨM ───────────────────────────────────────────────────
async function openEditProductModal(productId) {
  try {
    const res    = await fetch(`/api/products/${productId}`);
    const result = await res.json();

    if (!result.status) { showToast('❌ Không tìm thấy sản phẩm!'); return; }

    const p = result.data;

    document.getElementById('adminProductModalTitle').textContent = '✏️ Chỉnh sửa sản phẩm';
    document.getElementById('editProductId').value = p.id;
    document.getElementById('prodName').value      = p.name;
    document.getElementById('prodPrice').value     = p.price;
    document.getElementById('prodOldPrice').value  = p.old_price || '';
    document.getElementById('prodStock').value     = p.quantity;
    document.getElementById('prodEmoji').value     = p.emoji || '';
    document.getElementById('prodShop').value      = p.shop || '';
    document.getElementById('prodDesc').value      = p.description || '';

    // Load categories và chọn đúng danh mục hiện tại
    await loadCategoriesForProductModal(p.category_name);

    document.getElementById('adminProductModal').classList.add('show');

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ─── LOAD CATEGORIES VÀO DROPDOWN CỦA MODAL SẢN PHẨM ────────────────────────
async function loadCategoriesForProductModal(selectedName = null) {
  try {
    const res    = await fetch('/api/categories');
    const result = await res.json();
    if (!result.status) return;

    const select = document.getElementById('prodCategory');
    select.innerHTML = result.data.map(c => `
      <option value="${c.id}" ${selectedName === c.name ? 'selected' : ''}>${c.name}</option>
    `).join('');

  } catch (e) {
    console.error('Lỗi load categories cho modal:', e);
  }
}

// ─── LƯU SẢN PHẨM (THÊM MỚI HOẶC CẬP NHẬT) ─────────────────────────────────
async function handleSaveProduct(e) {
    e.preventDefault();

    const productId    = document.getElementById('editProductId').value;
    const isEdit       = !!productId;
    const isSellerMode = document.getElementById('editProductId').dataset.sellerMode === 'true';

    // ── 1. Lấy store_id ──────────────────────────────────────
    const storeId = isSellerMode
        ? currentUser?.store?.store_id
        : (document.getElementById('prodStoreId')?.value || 1);

    // ── 2. Validate cơ bản ───────────────────────────────────
    const name       = document.getElementById('prodName').value.trim();
    const price      = document.getElementById('prodPrice').value;
    const categoryId = document.getElementById('prodCategory').value;
    const emoji      = document.getElementById('prodEmoji').value.trim();

    if (!name)       { showToast('⚠️ Tên sản phẩm không được trống!');  return; }
    if (!price)      { showToast('⚠️ Giá sản phẩm không được trống!');  return; }
    if (!categoryId) { showToast('⚠️ Vui lòng chọn danh mục!');         return; }
    if (!emoji)      { showToast('⚠️ Vui lòng nhập emoji đại diện!');    return; }
    if (!storeId)    { showToast('⚠️ Không xác định được gian hàng!');   return; }

    // ── 3. CHECK QUYỀN SELLER — PHẢI Ở ĐÂY, TRƯỚC KHI GỌI API ──
    if (isSellerMode && isEdit) {
        try {
            const checkRes    = await fetch(`/api/products/${productId}`);
            const checkResult = await checkRes.json();

            if (!checkResult.status) {
                showToast('❌ Không tìm thấy sản phẩm!');
                return;
            }

            // So sánh store_id của sản phẩm với store của Seller đang đăng nhập
            if (checkResult.data.store_id !== currentUser?.store?.store_id) {
                showToast('❌ Bạn không có quyền sửa sản phẩm này!');
                return;
            }
        } catch (err) {
            showToast('❌ Lỗi kiểm tra quyền!');
            return;
        }
    }

    // ── 4. Build payload ─────────────────────────────────────
    const payload = {
        name        : name,
        price       : price,
        old_price   : document.getElementById('prodOldPrice').value || null,
        quantity    : document.getElementById('prodStock').value,
        emoji       : emoji,
        description : document.getElementById('prodDesc').value.trim(),
        category_id : categoryId,
        store_id    : storeId
    };

    // ── 5. Gọi API ───────────────────────────────────────────
    const url    = isEdit
        ? `/api/products/${productId}`
        : `/api/products`;
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res    = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.status) {
    showToast(isEdit ? '✅ Cập nhật thành công!' : '✅ Thêm sản phẩm thành công!');
    closeModal('adminProductModal');

    if (isSellerMode) {
        renderSellerProducts();
    } else {
        renderAdminProducts();
    }

    loadProducts();

    // ✅ Chỉ cần cập nhật dashboard khi thêm mới (không phải sửa)
    if (!isEdit) initAdminDashboard();
} else {
            showToast('❌ ' + result.message);
        }

    } catch (err) {
        showToast('❌ Lỗi kết nối!');
    }
}

// ─── RENDER DANH MỤC ADMIN ───────────────────────────────────────────────────
function hienThiMessageDanhMuc(message, ok) {
  const el = document.getElementById('catMessage');
  if (!el) return;
  el.style.display = 'block';
  el.textContent = message;
  el.style.color = ok ? 'var(--green)' : 'var(--red)';
}
async function renderAdminCategories() {
  const tbody = document.getElementById('tblCategoriesBody');
  tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:20px; color:var(--text-muted);">Đang tải...</td></tr>`;

  try {
    const res    = await fetch('/api/categories');
    const result = await res.json();

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">Chưa có danh mục nào</td></tr>`;
      return;
    }

    // 013: bộ lọc tìm kiếm — loc client theo tên trước khi vẽ bảng
    const keyword = (document.getElementById('catSearchFilter')?.value || '').trim().toLowerCase();
    let listLoc = result.data;
    if (keyword) listLoc = listLoc.filter(c => (c.name || '').toLowerCase().includes(keyword));

    if (!listLoc.length) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">Không tìm thấy kết quả</td></tr>`;
      return;
    }

    tbody.innerHTML = listLoc.map(c => `
      <tr>
        <td style="font-weight:600;">${c.name}</td>
        <td><code style="background:var(--bg); padding:2px 6px; border-radius:4px; font-size:12px;">${c.id}</code></td>
        <td>
          <button class="admin-action-btn btn-edit" onclick="editCategory(${c.id}, '${c.name.replace(/'/g, "\\'")}')">✏️ Sửa</button>
        </td>
      </tr>
    `).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
  }
}

// ─── THÊM DANH MỤC ───────────────────────────────────────────────────────────
async function addCategory() {
  const name = document.getElementById('newCatName').value.trim();
  if (!name) { hienThiMessageDanhMuc('⚠️ Tên danh mục không được trống!', false); return; }

  try {
    const res    = await fetch('/api/categories', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ name })
    });
    const result = await res.json();

    if (result.status) {
      hienThiMessageDanhMuc(result.message, true);
      document.getElementById('newCatName').value = '';
      renderAdminCategories();
      loadCategories(); // Cập nhật dropdown khắp nơi
    } else {
      hienThiMessageDanhMuc(result.message, false);
    }

  } catch (e) {
    hienThiMessageDanhMuc('❌ Lỗi kết nối!', false);
  }
}

// ─── SỬA DANH MỤC ────────────────────────────────────────────────────────────
async function editCategory(categoryId, currentName) {
  const newName = prompt(`Nhập tên mới cho danh mục:`, currentName);
  if (!newName || newName.trim() === currentName) return;

  try {
    const res    = await fetch(`/api/categories/${categoryId}`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ name: newName.trim() })
    });
    const result = await res.json();

    if (result.status) {
      hienThiMessageDanhMuc(result.message, true);
      renderAdminCategories();
      loadCategories();
    } else {
      hienThiMessageDanhMuc(result.message, false);
    }

  } catch (e) {
    hienThiMessageDanhMuc('❌ Lỗi kết nối!', false);
  }
}

// ─── XÓA DANH MỤC ────────────────────────────────────────────────────────────
async function deleteCategory(categoryId, categoryName) {
  if (!confirm(`Xóa danh mục "${categoryName}"?`)) return;

  try {
    const res = await fetch(`/api/categories/${categoryId}`, {
      method: 'DELETE'
    });
    const result = await res.json();

    if (result.status) {
      hienThiMessageDanhMuc(result.message, true);
      renderAdminCategories();
      loadCategories();
    } else {
      hienThiMessageDanhMuc(result.message, false);
    }

  } catch (e) {
    hienThiMessageDanhMuc('❌ Lỗi kết nối!', false);
  }
}
function openAddSellerProductModal() {
    // Reset form (dùng lại adminProductModal hoặc tạo modal riêng)
    document.getElementById('adminProductModalTitle').textContent = '➕ Thêm sản phẩm vào gian hàng';
    document.getElementById('editProductId').value = '';
    document.getElementById('prodName').value      = '';
    document.getElementById('prodPrice').value     = '';
    document.getElementById('prodOldPrice').value  = '';
    document.getElementById('prodStock').value     = '';
    document.getElementById('prodEmoji').value     = '';
    document.getElementById('prodDesc').value      = '';

    // Ghi nhớ đây là form của Seller để handleSaveProduct biết dùng store_id nào
    document.getElementById('editProductId').dataset.sellerMode = 'true';

    loadCategoriesForProductModal();
    document.getElementById('adminProductModal').classList.add('show');
}
function toggleEmojiPicker() {
  const picker = document.getElementById('emojiPicker');
  picker.style.display = picker.style.display === 'none' ? 'block' : 'none';

  // Lần đầu mở → render các emoji thành thẻ span có thể click
  if (picker.style.display === 'block' && !picker.dataset.rendered) {
    picker.querySelectorAll('.emoji-grid').forEach(grid => {
      const emojis = grid.textContent.trim().split(/\s+/);
      grid.innerHTML = emojis.map(em =>
        `<span onclick="selectEmoji('${em}')" title="${em}">${em}</span>`
      ).join('');
    });
    picker.dataset.rendered = 'true';
  }
}

function selectEmoji(emoji) {
  document.getElementById('prodEmoji').value = emoji;
  document.getElementById('emojiPicker').style.display = 'none';
}

// Đóng picker khi click ra ngoài
document.addEventListener('click', function(e) {
  const picker = document.getElementById('emojiPicker');
  if (picker && !picker.contains(e.target) && !e.target.closest('[onclick="toggleEmojiPicker()"]')) {
    picker.style.display = 'none';
  }
});
// ─── RENDER BẢNG QUẢN LÝ TÀI KHOẢN ──────────────────────────────────────────
async function renderAdminUsers() {
  const tbody = document.getElementById('tblAdminUsersBody');
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px;
                     color:var(--text-muted);">Đang tải...</td></tr>`;

  try {
    const res    = await fetch('/api/users');
    const result = await res.json();

    if (!result.status) {
      // 009 US3: Quản lý không có quyền xem danh sách đầy đủ (khoá/cấp lại vẫn qua endpoint riêng)
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                         color:var(--red);">🚫 ${result.message || 'Bạn không có quyền xem danh sách tài khoản!'}</td></tr>`;
      return;
    }

    if (!result.data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                         color:var(--text-muted);">Không có tài khoản nào</td></tr>`;
      return;
    }

    // 015 FR-005/012: Admin và Quản lý cùng xem danh sách; hành động theo vai trò
    const maQuyen  = currentUser ? (currentUser.ma_nhom_quyen || currentUser.Role_id) : 4;
    const laQuanLy = maQuyen === 2 || currentUser?.role === 'Quản lý';
    const laAdmin  = maQuyen === 1 || currentUser?.role === 'Admin';

    const roleFilter   = document.getElementById('userRoleFilter').value;
    const searchFilter = document.getElementById('userSearchFilter').value.toLowerCase();
    let data = result.data;

    if (searchFilter) {
      data = data.filter(u =>
        (u.ten_user    || '').toLowerCase().includes(searchFilter) ||
        (u.tendangnhap || '').toLowerCase().includes(searchFilter) ||
        (u.sdt         || '').includes(searchFilter)
      );
    }

    if (roleFilter !== 'all') {
      const targetRole = VAI_TRO_CHUAN.find(r =>
        r.RoleName.toLowerCase() === roleFilter.toLowerCase()
      );
      if (targetRole) data = data.filter(u => u.ma_nhom_quyen === targetRole.RoleId);
    }

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                         color:var(--text-muted);">Không tìm thấy kết quả</td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(u => {
      const roleName = getRoleName(u.ma_nhom_quyen);
      const roleCls  = getRoleCls(u.ma_nhom_quyen);
      const isMe     = u.ma_user === currentUser?.ma_user;

      // ✅ Đọc trang_thai từ backend — dùng class design system sẵn có
      const isBanned   = u.trang_thai === 'banned';
      const statusHtml = isBanned
        ? `<span class="user-status-banned">🔒 Đã khóa</span>`
        : `<span class="user-status-active">✅ Hoạt động</span>`;

      // 017: Quản lý chỉ khóa/mở + cấp lại mật khẩu cho Seller/Khách hàng
      let hanhDong = '';
      if (isMe) {
        hanhDong = `<span style="font-size:12px; color:var(--text-muted);">Tài khoản của bạn</span>`;
      } else if (laQuanLy && (u.ma_nhom_quyen === 3 || u.ma_nhom_quyen === 4)) {
        hanhDong = `
          <button class="admin-action-btn ${isBanned ? 'btn-edit' : 'btn-cancel'}"
                  onclick="capNhatTrangThaiNhanh(${u.ma_user}, '${isBanned ? 'active' : 'banned'}')">
            ${isBanned ? '🔓 Mở khóa' : '🔒 Khóa'}
          </button>
          <button class="admin-action-btn btn-confirm"
                  onclick="moModalCapLaiMatKhau(${u.ma_user}, '${u.ten_user.replace(/'/g, "\\'")}')">
            🔑 Cấp lại mật khẩu
          </button>`;
      } else {
        hanhDong = `<span style="font-size:12px; color:var(--text-muted);">Chỉ xem</span>`;
      }

      return `
        <tr style="${isBanned ? 'opacity:0.6;' : ''}">
          <td style="font-weight:700; color:var(--text-muted);">#${u.ma_user}</td>
          <td>
            <div style="font-weight:600;">${u.ten_user}</div>
            <div style="font-size:11px; color:var(--text-muted);">@${u.tendangnhap}</div>
          </td>
          <td style="font-size:13px; color:var(--text-secondary);">${u.tendangnhap}</td>
          <td style="font-size:13px;">${u.sdt || '—'}</td>
          <td><span class="role-badge ${roleCls}">${roleName}</span></td>
          <td>${statusHtml}</td>
          <td>${hanhDong}</td>
        </tr>
      `;
    }).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                       color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
  }
}

// ─── MỞ MODAL CHỈNH SỬA USER ─────────────────────────────────────────────────
async function loadCartFromServer() {
  if (!currentUser) return;
  try {
    const userId = currentUser.ma_user || currentUser.UserId;
    const res    = await fetch(`/api/gio-hang/${userId}`);
    const result = await res.json();

    if (result.status === true && Array.isArray(result.data)) {
      // Map về đúng cấu trúc mà handlePlaceOrder cần
      cart = result.data.map(item => ({
        ProductId  : item.ProductId   || item.product_id,
        ProductName: item.ProductName || item.product_name || item.name || `Sản phẩm #${item.ProductId || item.product_id}`,
        Emoji      : item.Emoji       || item.emoji        || '📦',
        ImageUrl  : item.ImageUrl || item.image_url || '',
        StoreId   : item.StoreId   || item.store_id,
        Quantity   : item.Quantity    || item.quantity     || 1,
        UnitPrice  : item.UnitPrice   || item.unit_price   || item.price || 0,
        TotalPrice : (item.Quantity   || item.quantity || 1) *
                     (item.UnitPrice  || item.unit_price || item.price || 0)
      }));
      updateCartBadge();
      console.log(`✅ Đã load ${cart.length} sản phẩm trong giỏ hàng`);
    } else {
      cart = [];
      updateCartBadge();
    }
  } catch (e) {
    console.error('Lỗi load giỏ hàng:', e);
    cart = [];
  }
}
async function addToCart(productId, quantity, unitPrice) {
    if (!currentUser) {
        showToast("⚠️ Vui lòng đăng nhập để mua hàng!");
        openAuthModal();
        return;
    }
    await xuLyThemVaoGio(productId, quantity, unitPrice, false);
}

async function xuLyThemVaoGio(productId, quantity, unitPrice, force) {
    try {
        const res = await fetch('/api/gio-hang/them', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                UserId   : currentUser.ma_user || currentUser.UserId,
                ProductId: productId,
                Quantity : quantity,
                UnitPrice: unitPrice
            })
        });
        const result = await res.json();

        if (result.status === true) {
            showToast("🛒 " + result.message);
            loadCartFromServer();
            return;
        }

        showToast("❌ " + result.message);

    } catch (e) {
        showToast("❌ Lỗi kết nối Server!");
    }
}
async function handlePlaceOrder(e) {
  e.preventDefault();

  const receiverName    = document.getElementById('chkName').value.trim();
  const receiverPhone   = document.getElementById('chkPhone').value.trim();
  const receiverAddress = document.getElementById('chkAddress').value.trim();
  const paymentMethod   = document.getElementById('chkPayment').value;

  if (!receiverName || !receiverPhone || !receiverAddress) {
    showToast('⚠️ Vui lòng điền đầy đủ thông tin giao hàng!');
    return;
  }

  const subtotal    = cart.reduce((sum, item) => sum + (item.Quantity * item.UnitPrice), 0);
  const totalAmount = Math.max(0, subtotal + currentShippingFee);

  // Debug: kiểm tra cấu trúc cart trước khi gửi
  console.log("Cart hiện tại:", JSON.stringify(cart, null, 2));

  const orderPayload = {
    UserId         : currentUser.ma_user || currentUser.UserId,
    ReceiverName   : receiverName,
    ReceiverPhone  : receiverPhone,
    ShippingAddress: receiverAddress,
    PaymentMethod  : paymentMethod,
    SubTotal       : subtotal,
    ShippingFee    : currentShippingFee,
    TotalAmount    : totalAmount,
    Items: cart.map(item => ({
      // Thử tất cả các tên field có thể có
      ProductId  : item.ProductId   || item.product_id  || item.id,
      ProductName: item.ProductName || item.product_name|| item.name || 'Sản phẩm',
      Emoji      : item.Emoji       || item.emoji        || '📦',
      Quantity   : item.Quantity    || item.quantity     || 1,
      UnitPrice  : item.UnitPrice   || item.unit_price   || item.price || 0,
      TotalPrice : (item.Quantity   || item.quantity     || 1) *
                   (item.UnitPrice  || item.unit_price   || item.price || 0)
    }))
  };

  console.log("Payload gửi lên:", JSON.stringify(orderPayload, null, 2));

  try {
    const response = await fetch('/api/don-hang/dat-hang', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(orderPayload)
    });
    const result = await response.json();

    if (result.status === true) {
      showToast('🎉 ' + result.message);
      closeModal('checkoutModal');
      closeCart();
      cart = [];
      currentShippingFee = 25000;
      updateCartBadge();
      renderCartItems();
      // 011 US2: đặt hàng có thể sinh NHIỀU đơn theo từng shop (data.orders)
      const data = result.data || {};
      const orders = data.orders || [];
      if (orders.length > 0) {
        hienThiHoaDonNhieuDon(orders);
      } else if (Array.isArray(data.order_ids) && data.order_ids.length > 0) {
        hienThiHoaDon(data.order_ids[0]);
      }
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi hệ thống khi đặt hàng!');
    console.error(e);
  }
}
// ─── RENDER GIAO DIỆN GIỎ HÀNG ─────────────────────────────────────────────
// ── 005 US3: hóa đơn sau thanh toán + mở lại từ lịch sử ──
// ── 011 US2: hóa đơn NHIỀU đơn (tách theo shop) sau khi đặt hàng ──
async function hienThiHoaDonNhieuDon(orders) {
  const box = document.getElementById('invoiceContent');
  if (!box) return;
  const tongChung = orders.reduce((s, o) => s + (Number(o.total) || 0), 0);
  box.innerHTML = `
    <div style="font-size:13px; line-height:1.9;">
      <div style="font-weight:700; margin-bottom:6px;">Đơn hàng đã tách theo từng shop:</div>
      ${orders.map(o => `
        <div style="display:flex; justify-content:space-between; gap:8px;
                    border-bottom:1px solid var(--border); padding:6px 0;">
          <span>🧾 Đơn #${o.order_id} — <b>${o.store_name || ('Shop #' + o.store_id)}</b></span>
          <span style="font-weight:600;">${Number(o.total || 0).toLocaleString('vi-VN')}đ</span>
        </div>`).join('')}
      <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:15px; margin-top:10px;">
        <span>Tổng cộng (${orders.length} đơn):</span>
        <span style="color:var(--red);">${tongChung.toLocaleString('vi-VN')}đ</span>
      </div>
    </div>`;
  document.getElementById('invoiceModal').classList.add('show');
}

async function hienThiHoaDon(orderId) {
  try {
    const res = await fetch(`/api/don-hang/hoa-don/${orderId}`);
    const result = await res.json();
    if (!result.status) {
      showToast('❌ ' + (result.message || 'Không thể tải hóa đơn!'));
      return;
    }
    const d = result.data;
    const items = d.Items || d.items || [];
    const box = document.getElementById('invoiceContent');
    if (box) {
      box.innerHTML = `
        <div style="font-size:13px; line-height:1.8;">
          <div><b>Mã đơn:</b> #${d.OrderId}</div>
          <div><b>Trạng thái:</b> ${d.Status}</div>
          <div><b>Người nhận:</b> ${d.ReceiverName} — ${d.ReceiverPhone}</div>
          <div><b>Địa chỉ:</b> ${d.ShippingAddress}</div>
          <div><b>Thanh toán:</b> ${d.PaymentMethod}</div>
          <hr style="border:none; border-top:1px solid var(--border); margin:10px 0;">
          ${items.map(it => `
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
              <span>${it.ProductName || it.product_name} × ${it.Quantity || it.quantity}</span>
              <span>${Number(it.TotalPrice || it.total_price || 0).toLocaleString('vi-VN')}đ</span>
            </div>`).join('')}
          <hr style="border:none; border-top:1px solid var(--border); margin:10px 0;">
          <div style="display:flex; justify-content:space-between;"><span>Tạm tính:</span><span>${Number(d.SubTotal || 0).toLocaleString('vi-VN')}đ</span></div>
          <div style="display:flex; justify-content:space-between;"><span>Phí ship:</span><span>${Number(d.ShippingFee || 0).toLocaleString('vi-VN')}đ</span></div>
          <div style="display:flex; justify-content:space-between;"><span>Giảm giá:</span><span>-${Number(d.DiscountAmount || 0).toLocaleString('vi-VN')}đ</span></div>
          <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:15px; margin-top:6px;"><span>Tổng cộng:</span><span style="color:var(--red);">${Number(d.TotalAmount || 0).toLocaleString('vi-VN')}đ</span></div>
        </div>`;
      document.getElementById('invoiceModal').classList.add('show');
    }
  } catch (e) {
    showToast('❌ Lỗi tải hóa đơn!');
  }
}
function renderCartItems() {
  const container = document.getElementById('cartItemsList');

  if (!cart || cart.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:40px 20px; color:var(--text-muted);">
        <div style="font-size:40px; margin-bottom:10px;">🛒</div>
        <p>Giỏ hàng của bạn đang trống</p>
      </div>`;
    document.getElementById('cartSubtotalText').textContent = '0đ';
    document.getElementById('cartTotalText').textContent    = '0đ';
    return;
  }

  container.innerHTML = cart.map(item => `
    <div style="display:flex; gap:12px; padding:12px 0;
                border-bottom:1px solid var(--border); align-items:flex-start;">

      <!-- Emoji sản phẩm -->
      <div style="width:60px;height:60px;flex-shrink:0;">
        ${
          item.ImageUrl
            ? `<img src="/static/${item.ImageUrl}"
                    style="width:60px;
                          height:60px;
                          object-fit:cover;
                          border-radius:8px;">`
            : (item.Emoji || '📦')
        }
      </div>
      <!-- Tên + điều chỉnh số lượng -->
      <div style="flex:1; min-width:0;">
        <div style="font-weight:600; font-size:14px; margin-bottom:4px;
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
          ${item.ProductName || 'Sản phẩm #' + item.ProductId}
        </div>
        <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">
          ${Number(item.UnitPrice).toLocaleString('vi-VN')}đ / sản phẩm
        </div>

        <!-- Nút tăng / giảm số lượng -->
        <div style="display:flex; align-items:center; gap:8px;">
          <button onclick="changeCartQty(${item.ProductId}, ${item.Quantity - 1})"
            style="width:28px; height:28px; border-radius:6px; border:1px solid var(--border);
                   background:var(--bg); cursor:pointer; font-size:16px; font-weight:700;
                   display:flex; align-items:center; justify-content:center;">−</button>

          <span style="min-width:24px; text-align:center; font-weight:700;">
            ${item.Quantity}
          </span>

          <button onclick="changeCartQty(${item.ProductId}, ${item.Quantity + 1})"
            style="width:28px; height:28px; border-radius:6px; border:1px solid var(--border);
                   background:var(--bg); cursor:pointer; font-size:16px; font-weight:700;
                   display:flex; align-items:center; justify-content:center;">+</button>
        </div>
      </div>

      <!-- Tổng tiền + nút xóa -->
      <div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px; flex-shrink:0;">
        <div style="font-weight:700; color:var(--red); font-size:15px;">
          ${Number(item.Quantity * item.UnitPrice).toLocaleString('vi-VN')}đ
        </div>
        <button onclick="xoaKhoiGio(${item.ProductId})"
          style="background:none; border:none; color:var(--text-muted);
                 cursor:pointer; font-size:18px; line-height:1;"
          title="Xóa sản phẩm">🗑️</button>
      </div>
    </div>
  `).join('');

  const subtotal = cart.reduce((s, i) => s + i.Quantity * i.UnitPrice, 0);
  document.getElementById('cartSubtotalText').textContent =
    subtotal.toLocaleString('vi-VN') + 'đ';
  document.getElementById('cartTotalText').textContent =
    subtotal.toLocaleString('vi-VN') + 'đ';
}

// ─── Xóa 1 sản phẩm khỏi giỏ ────────────────────────────────
async function xoaKhoiGio(productId) {
  if (!currentUser) return;
  try {
    const res    = await fetch('/api/gio-hang/xoa', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({
        UserId   : currentUser.ma_user || currentUser.UserId,
        ProductId: productId
      })
    });
    const result = await res.json();
    if (result.status) {
      await loadCartFromServer();
      renderCartItems();
      showToast('🗑️ Đã xóa sản phẩm khỏi giỏ hàng!');
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ─── Tăng/giảm số lượng ──────────────────────────────────────
async function changeCartQty(productId, newQty) {
  if (!currentUser) return;

  // Nếu newQty = 0 → xóa luôn
  if (newQty === 0) {
    if (!confirm('Xóa sản phẩm này khỏi giỏ hàng?')) return;
    await xoaKhoiGio(productId);
    return;
  }

  try {
    const res    = await fetch('/api/gio-hang/cap-nhat', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({
        UserId   : currentUser.ma_user || currentUser.UserId,
        ProductId: productId,
        Quantity : newQty
      })
    });
    const result = await res.json();
    if (result.status) {
      await loadCartFromServer();
      renderCartItems();
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// Bật/tắt khung giỏ hàng
function openCart() {
    document.getElementById('cartOverlay').classList.add('show');
    renderCartItems(); // Vẽ lại mỗi khi mở lên
}

function closeCart() {
    document.getElementById('cartOverlay').classList.remove('show');
}
function getShippingFee(buyerCity) {
  return buyerCity === SELLER_CITY ? 25000 : 40000;
}

function getSoShopTrongGio() {
  const cacStoreId = cart.map(item => item.StoreId).filter(sid => sid !== undefined && sid !== null);
  return new Set(cacStoreId).size;
}

function recalcOrderTotal() {
  const buyerCity = document.getElementById('chkBuyerCity').value;
  const phiCoBan = getShippingFee(buyerCity);
  const soShop = Math.max(1, getSoShopTrongGio());
  currentShippingFee = phiCoBan * soShop;

  const isSame = buyerCity === SELLER_CITY;
  document.getElementById('shippingNote').textContent = isSame
    ? 'Phí vận chuyển nội thành:'
    : 'Phí vận chuyển liên tỉnh:';
  document.getElementById('shippingFeeDisplay').textContent =
    currentShippingFee.toLocaleString('vi-VN') + 'đ';

  updateCheckoutSummary();
}

function updateCheckoutSummary() {
  const subtotal = cart.reduce((sum, item) => sum + (item.Quantity * item.UnitPrice), 0);
  const total = subtotal + currentShippingFee;

  document.getElementById('checkoutSubtotalText').textContent =
    subtotal.toLocaleString('vi-VN') + 'đ';
  document.getElementById('checkoutShipText').textContent =
    currentShippingFee.toLocaleString('vi-VN') + 'đ';
  document.getElementById('checkoutTotalText').textContent =
    Math.max(0, total).toLocaleString('vi-VN') + 'đ';
}

function togglePaymentDetails(val) {
  document.getElementById('bankDetailsBlock').style.display = val === 'Bank'    ? 'block' : 'none';
  document.getElementById('momoBlock').style.display        = val === 'Momo'    ? 'block' : 'none';
  document.getElementById('zalopayBlock').style.display     = val === 'VNPay' ? 'block' : 'none';
}

function openCheckoutModal() {
  if (!currentUser) {
    showToast('⚠️ Vui lòng đăng nhập để đặt hàng!');
    openAuthModal();
    return;
  }
  if (!cart || cart.length === 0) {
    showToast('⚠️ Giỏ hàng đang trống!');
    return;
  }

  // Điền thông tin mặc định từ user
  document.getElementById('chkName').value    = currentUser.ten_user || '';
  document.getElementById('chkPhone').value   = currentUser.sdt || '';
  document.getElementById('chkAddress').value = currentUser.dia_chi || '';

  // Tóm tắt giỏ hàng
  const summaryEl = document.getElementById('checkoutCartSummary');
  summaryEl.innerHTML = cart.map(item => `
    <div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid var(--border); font-size:12px;">
      <span>${item.ProductName} x${item.Quantity}</span>
      <span style="font-weight:600;">${(item.Quantity * item.UnitPrice).toLocaleString('vi-VN')}đ</span>
    </div>
  `).join('');

  // Tính phí ship ban đầu & cập nhật tổng
  currentShippingFee = 25000; // mặc định nội thành
  recalcOrderTotal();

  document.getElementById('checkoutModal').classList.add('show');
}
// ==========================================
// ADMIN - QUẢN LÝ ĐƠN HÀNG
// ==========================================

const ORDER_STATUS_MAP = {
  'Pending'  : { label: 'Chờ duyệt',    cls: 'status-pending'   },
  'Confirmed': { label: 'Đã xác nhận',  cls: 'status-confirmed' },
  'Shipping' : { label: 'Đang giao',    cls: 'status-shipping'  },
  'Completed': { label: 'Hoàn thành',   cls: 'status-done'      },
  'Cancelled': { label: 'Đã hủy',       cls: 'status-cancelled' },
};

// Lưu toàn bộ đơn hàng để filter không cần gọi lại API
let allAdminOrders = [];

async function renderAdminOrders() {
  const tbody    = document.getElementById('tblAdminOrdersBody');
  const filterStatus = document.getElementById('orderFilterStatus').value;

  // Chỉ gọi API lần đầu hoặc khi chưa có data
  if (allAdminOrders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                       padding:20px; color:var(--text-muted);">Đang tải...</td></tr>`;
    try {
      const res    = await fetch('/api/don-hang/tat-ca');
      const result = await res.json();
      allAdminOrders = result.status ? result.data : [];
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                         color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
      return;
    }
  }

  // Lọc theo status
  const filtered = filterStatus === 'all'
    ? allAdminOrders
    : allAdminOrders.filter(o => o.Status?.toLowerCase() === filterStatus);

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                       color:var(--text-muted);">Không có đơn hàng nào</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(o => {
    const statusInfo = ORDER_STATUS_MAP[o.Status] || { label: o.Status, cls: '' };
    const itemSummary = (o.Items || [])
      .map(i => `${i.Emoji || '📦'} ${i.ProductName} x${i.Quantity}`)
      .join('<br>');
    const createdAt = o.CreatedAt
      ? new Date(o.CreatedAt).toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
      : '—';

    return `
      <tr>
        <td style="font-weight:700; color:var(--text-muted);">#${o.OrderId}</td>
        <td>
          <div style="font-weight:600;">${o.ReceiverName}</div>
          <div style="font-size:11px; color:var(--text-muted);">📞 ${o.ReceiverPhone}</div>
          <div style="font-size:11px; color:var(--text-muted);">👤 ${o.CustomerName || '—'}</div>
        </td>
        <td style="font-size:12px; max-width:180px;">${itemSummary || '—'}</td>
        <td style="font-weight:700; color:var(--red);">
          ${Number(o.TotalAmount).toLocaleString('vi-VN')}đ
          <div style="font-size:11px; color:var(--text-muted); font-weight:400;">
            Ship: ${Number(o.ShippingFee || 0).toLocaleString('vi-VN')}đ
          </div>
        </td>
        <td><span class="badge-status ${statusInfo.cls}">${statusInfo.label}</span></td>
        <td style="font-size:12px;">${createdAt}</td>
        <td>
          ${o.Status === 'Pending' ? `
            <button class="admin-action-btn btn-confirm"
              onclick="capNhatTrangThaiDon(${o.OrderId}, 'Confirmed')">✅ Duyệt</button>
            <button class="admin-action-btn btn-cancel"
              onclick="capNhatTrangThaiDon(${o.OrderId}, 'Cancelled')">❌ Hủy</button>
          ` : ''}
          ${o.Status === 'Confirmed' ? `
            <button class="admin-action-btn btn-confirm"
              onclick="capNhatTrangThaiDon(${o.OrderId}, 'Shipping')">🚚 Giao hàng</button>
          ` : ''}
          ${o.Status === 'Shipping' ? `
            <button class="admin-action-btn btn-confirm"
              onclick="capNhatTrangThaiDon(${o.OrderId}, 'Completed')">🏁 Hoàn thành</button>
          ` : ''}
          ${o.Status === 'Completed' || o.Status === 'Cancelled' ? `
            <span style="font-size:12px; color:var(--text-muted);">—</span>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

async function capNhatTrangThaiDon(orderId, newStatus) {
  const statusLabel = ORDER_STATUS_MAP[newStatus]?.label || newStatus;
  if (!confirm(`Xác nhận chuyển đơn #${orderId} sang: "${statusLabel}"?`)) return;

  try {
    const res    = await fetch(`/api/don-hang/${orderId}/trang-thai`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ status: newStatus })
    });
    const result = await res.json();

    if (result.status) {
      showToast(`✅ ${result.message}`);
      const idx = allAdminOrders.findIndex(o => o.OrderId === orderId);
      if (idx !== -1) allAdminOrders[idx].Status = newStatus;
      renderAdminOrders();

      // ← Thêm dòng này: cập nhật ngay số liệu doanh thu/đơn hàng trên Dashboard
      initAdminDashboard();

    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
// ==========================================
// LỊCH SỬ ĐƠN HÀNG
// ==========================================

let allUserOrders = []; // Cache đơn hàng của user

const ORDER_STATUS_CONFIG = {
  'Pending'  : { label: 'Chờ duyệt',   cls: 'status-pending',   icon: '🕐' },
  'Confirmed': { label: 'Đã xác nhận', cls: 'status-confirmed', icon: '✅' },
  'Shipping' : { label: 'Đang giao',   cls: 'status-shipping',  icon: '🚚' },
  'Completed': { label: 'Hoàn thành',  cls: 'status-done',      icon: '🏁' },
  'Cancelled': { label: 'Đã hủy',      cls: 'status-cancelled', icon: '❌' },
};

// Mở modal lịch sử đơn hàng
async function openOrderHistoryModal() {
  if (!currentUser) {
    showToast('⚠️ Vui lòng đăng nhập!');
    openAuthModal();
    return;
  }
  document.getElementById('orderHistoryModal').classList.add('show');
  document.getElementById('historyFilterStatus').value = 'all';
  await loadUserOrders();
}

// Tải đơn hàng từ API
async function loadUserOrders() {
  const container = document.getElementById('orderHistoryContent');
  container.innerHTML = `
    <div style="text-align:center; padding:30px; color:var(--text-muted);">
      ⏳ Đang tải lịch sử đơn hàng...
    </div>`;

  try {
    const userId = currentUser.ma_user || currentUser.UserId;
    const res    = await fetch(`/api/don-hang/cua-toi/${userId}`);
    const result = await res.json();

    allUserOrders = result.status ? (result.data || []) : [];
    renderOrderHistoryList(allUserOrders);
  } catch (e) {
    container.innerHTML = `
      <div style="text-align:center; padding:30px; color:var(--red);">
        ❌ Lỗi tải dữ liệu. Vui lòng thử lại!
      </div>`;
  }
}

// Lọc theo trạng thái
function filterOrderHistory() {
  const status   = document.getElementById('historyFilterStatus').value;
  const filtered = status === 'all'
    ? allUserOrders
    : allUserOrders.filter(o => o.Status === status);
  renderOrderHistoryList(filtered);
}

// Render danh sách đơn hàng trong modal
function renderOrderHistoryList(orders) {
  const container = document.getElementById('orderHistoryContent');

  if (!orders || orders.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:40px; color:var(--text-muted);">
        <div style="font-size:40px; margin-bottom:10px;">📭</div>
        <p>Bạn chưa có đơn hàng nào</p>
        <button onclick="closeModal('orderHistoryModal')"
          style="margin-top:10px; background:var(--primary); color:white;
                 border:none; border-radius:8px; padding:8px 20px; cursor:pointer; font-family:inherit;">
          Mua sắm ngay →
        </button>
      </div>`;
    return;
  }

  container.innerHTML = orders.map(o => {
    const s = ORDER_STATUS_CONFIG[o.Status] || { label: o.Status, cls: '', icon: '📦' };
    const createdAt = o.CreatedAt
      ? new Date(o.CreatedAt).toLocaleDateString('vi-VN', {
          day: '2-digit', month: '2-digit', year: 'numeric',
          hour: '2-digit', minute: '2-digit'
        })
      : '—';

    const itemList = (o.Items || []).map(i => `
      <div style="display:flex; justify-content:space-between; align-items:center;
                  padding:6px 0; border-bottom:1px solid var(--border); font-size:13px;">
        <span>${i.Emoji || '📦'} ${i.ProductName || 'Sản phẩm'} 
          <span style="color:var(--text-muted);">x${i.Quantity}</span>
        </span>
        <span style="font-weight:600;">
          ${Number(i.TotalPrice || 0).toLocaleString('vi-VN')}đ
        </span>
      </div>
    `).join('');

    return `
      <div style="background:var(--white); border:1px solid var(--border);
                  border-radius:10px; margin-bottom:14px; overflow:hidden;">

        <!-- Header đơn hàng -->
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:10px 14px; background:var(--bg); border-bottom:1px solid var(--border);">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-weight:700; font-size:14px;">Đơn #${o.OrderId}</span>
            <span class="badge-status ${s.cls}" style="font-size:11px;">
              ${s.icon} ${s.label}
            </span>
          </div>
          <span style="font-size:12px; color:var(--text-muted);">🕐 ${createdAt}</span>
        </div>

        <!-- Danh sách sản phẩm -->
        <div style="padding:10px 14px;">
          ${itemList || '<div style="color:var(--text-muted); font-size:13px;">Không có sản phẩm</div>'}
        </div>

        <!-- Footer: địa chỉ + tổng tiền -->
        <div style="padding:10px 14px; border-top:1px solid var(--border);
                    display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:8px;">
          <div style="font-size:12px; color:var(--text-muted); max-width:380px;">
            <div>📍 ${o.ShippingAddress || '—'}</div>
            <div>💳 ${o.PaymentMethod || '—'}</div>
            ${Number(o.ShippingFee || 0) > 0
              ? `<div>🚚 Phí ship: ${Number(o.ShippingFee).toLocaleString('vi-VN')}đ</div>`
              : ''}
            ${Number(o.DiscountAmount || 0) > 0
              ? `<div style="color:var(--green);">🎟️ Giảm: -${Number(o.DiscountAmount).toLocaleString('vi-VN')}đ</div>`
              : ''}
          </div>
          <div style="text-align:right;">
            <div style="font-size:12px; color:var(--text-muted);">Tổng thanh toán</div>
            <div style="font-size:18px; font-weight:800; color:var(--red);">
              ${Number(o.TotalAmount || 0).toLocaleString('vi-VN')}đ
            </div>
          </div>
        </div>

        <!-- Nút hành động nếu có thể hủy -->
        ${o.Status === 'Pending' ? `
          <div style="padding:8px 14px; border-top:1px solid var(--border); text-align:right; display:flex; gap:8px; justify-content:flex-end;">
            <button onclick="hienThiHoaDon(${o.OrderId})"
              style="background:var(--primary); border:none; color:white;
                     border-radius:6px; padding:5px 14px; cursor:pointer;
                     font-family:inherit; font-size:13px;">
              🧾 Xem hóa đơn
            </button>
            <button onclick="huyDonHangCuaToi(${o.OrderId})"
              style="background:none; border:1px solid var(--red); color:var(--red);
                     border-radius:6px; padding:5px 14px; cursor:pointer;
                     font-family:inherit; font-size:13px;">
              ❌ Hủy đơn hàng
            </button>
          </div>
        ` : `
          <div style="padding:8px 14px; border-top:1px solid var(--border); text-align:right;">
            <button onclick="hienThiHoaDon(${o.OrderId})"
              style="background:none; border:1px solid var(--primary); color:var(--primary);
                     border-radius:6px; padding:5px 14px; cursor:pointer;
                     font-family:inherit; font-size:13px;">
              🧾 Xem hóa đơn
            </button>
          </div>
        `}
      </div>
    `;
  }).join('');
}

// Hủy đơn từ phía khách hàng (chỉ khi Pending)
async function huyDonHangCuaToi(orderId) {
  if (!confirm(`Xác nhận hủy đơn hàng #${orderId}?`)) return;
  try {
    const res    = await fetch(`/api/don-hang/${orderId}/trang-thai`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ status: 'Cancelled' })
    });
    const result = await res.json();
    if (result.status) {
      showToast('✅ Đã hủy đơn hàng!');
      await loadUserOrders(); // Reload lại
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// Render preview 2 đơn gần nhất ngoài trang chủ
async function renderRecentOrdersPreview() {
  const section   = document.getElementById('orderHistorySection');
  const container = document.getElementById('recentOrdersPreview');
  if (!section || !container || !currentUser) return;

  try {
    const userId = currentUser.ma_user || currentUser.UserId;
    const res    = await fetch(`/api/don-hang/cua-toi/${userId}`);
    const result = await res.json();
    const orders = result.status ? (result.data || []) : [];

    if (orders.length === 0) {
      section.style.display = 'none';
      return;
    }

    section.style.display = 'block';
    const recent = orders.slice(0, 2); // Chỉ hiện 2 đơn gần nhất

    container.innerHTML = recent.map(o => {
      const s = ORDER_STATUS_CONFIG[o.Status] || { label: o.Status, cls: '', icon: '📦' };
      const firstItem = (o.Items || [])[0];
      const moreCount = (o.Items || []).length - 1;

      return `
        <div style="background:var(--white); border:1px solid var(--border);
                    border-radius:8px; padding:10px 14px; margin-bottom:8px;
                    display:flex; justify-content:space-between; align-items:center;
                    cursor:pointer;" onclick="openOrderHistoryModal()">
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:24px;">${firstItem?.Emoji || '📦'}</div>
            <div>
              <div style="font-weight:600; font-size:13px;">
                ${firstItem?.ProductName || 'Sản phẩm'}
                ${moreCount > 0 ? `<span style="color:var(--text-muted); font-weight:400;">+${moreCount} sản phẩm khác</span>` : ''}
              </div>
              <div style="font-size:11px; color:var(--text-muted);">
                Đơn #${o.OrderId} · <span class="badge-status ${s.cls}">${s.icon} ${s.label}</span>
              </div>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700; color:var(--red); font-size:14px;">
              ${Number(o.TotalAmount || 0).toLocaleString('vi-VN')}đ
            </div>
            <div style="font-size:11px; color:var(--primary);">Xem chi tiết →</div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    section.style.display = 'none';
  }
}
// 4 vai trò chuẩn theo seed mới (FR-001): 1=Admin, 2=Quản lý, 3=Seller, 4=Customer
const VAI_TRO_CHUAN = [
  { RoleId: 1, RoleName: 'Admin' },
  { RoleId: 2, RoleName: 'Quản lý' },
  { RoleId: 3, RoleName: 'Seller' },
  { RoleId: 4, RoleName: 'Customer' },
];

// Lấy tên role theo ID — dùng trong renderAdminUsers
function getRoleName(roleId) {
  const r = VAI_TRO_CHUAN.find(r => r.RoleId === roleId);
  return r ? r.RoleName : `Vai trò #${roleId}`;
}

// Lấy class badge theo ID — có thể mở rộng sau
function getRoleCls(roleId) {
  if (roleId === 1 || roleId === 2) return 'role-admin';
  if (roleId === 3) return 'role-seller';
  return 'role-customer'; // mặc định
}

// ─── RENDER BẢNG QUẢN LÝ TÀI KHOẢN (ĐỘNG) ───────────────────

// ─── MỞ MODAL CHỈNH SỬA USER — DROPDOWN VAI TRÒ TĨNH ─────────
async function openEditUserModal(ma_user, ten_user, ma_nhom_quyen, currentStatus = 'active') {
  document.getElementById('editUserId').value = ma_user;

  document.getElementById('editUserInfo').innerHTML = `
    <div style="display:flex; align-items:center; gap:10px;">
      <div style="width:40px; height:40px; border-radius:50%; background:var(--primary-light);
                  display:flex; align-items:center; justify-content:center;
                  font-size:18px; font-weight:700; color:var(--primary);">
        ${ten_user.charAt(0).toUpperCase()}
      </div>
      <div>
        <div style="font-weight:700;">${ten_user}</div>
        <div style="font-size:12px; color:var(--text-muted);">ID: #${ma_user}</div>
      </div>
    </div>
  `;

  // Vai trò hiển thị chỉ đọc — không cho sửa role qua modal (feature 002)
  const roleInput = document.getElementById('editUserRoleReadonly');
  if (roleInput) {
    roleInput.value = getRoleName(ma_nhom_quyen);
  }

  // ✅ Set đúng trạng thái hiện tại
  document.getElementById('editUserStatus').value = currentStatus;

  document.getElementById('adminUserModal').classList.add('show');
}
async function renderUserRoleFilter() {
  const select = document.getElementById('userRoleFilter');
  if (!select) return;
  select.innerHTML = `<option value="all">Tất cả vai trò</option>` +
    VAI_TRO_CHUAN.map(r => `<option value="${r.RoleName}">${r.RoleName}</option>`).join('');
}

// ─── LƯU THAY ĐỔI TRẠNG THÁI TÀI KHOẢN ──────────────────────────────────────
// 009 US3: nút Khóa/Mở khóa nhanh trong bảng tài khoản (chỉ Quản lý)
async function capNhatTrangThaiNhanh(ma_user, trang_thai_moi) {
  if (!ma_user) { showToast('⚠️ Thiếu thông tin!'); return; }
  try {
    const res = await fetch(`/api/users/${ma_user}/status`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ status: trang_thai_moi })
    });
    const result = await res.json();
    if (result.status) {
      showToast(trang_thai_moi === 'banned' ? '🔒 Đã khóa tài khoản!' : '🔓 Đã mở khóa tài khoản!');
      renderAdminUsers();
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function handleSaveUserRole() {
  const ma_user   = document.getElementById('editUserId').value;
  const newStatus = document.getElementById('editUserStatus').value;

  if (!ma_user) { showToast('⚠️ Thiếu thông tin!'); return; }

  try {
    const resStatus = await fetch(`/api/users/${ma_user}/status`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ status: newStatus })
    });
    const rStatus = await resStatus.json();

    if (rStatus.status) {
      showToast('✅ Đã cập nhật trạng thái!');
      closeModal('adminUserModal');
      renderAdminUsers();
    } else {
      showToast('❌ ' + rStatus.message);
    }
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ─── CẤP LẠI MẬT KHẨU (FR-010 / FR-011) ─────────────────────────────────────
function moModalCapLaiMatKhau(ma_user = null, ten_user = '') {
  const maUserHienTai = ma_user || document.getElementById('editUserId').value;
  if (!maUserHienTai) { showToast('⚠️ Thiếu thông tin!'); return; }

  document.getElementById('resetUserId').value = maUserHienTai;
  if (ten_user) {
    document.getElementById('resetUserInfo').innerHTML =
      `<div style="font-weight:700;">${ten_user}</div>
       <div style="font-size:12px; color:var(--text-muted);">ID: #${maUserHienTai}</div>`;
  } else if (document.getElementById('editUserInfo')) {
    document.getElementById('resetUserInfo').innerHTML =
      document.getElementById('editUserInfo').innerHTML;
  }
  document.getElementById('resetPasswordInput').value = '';
  document.getElementById('resetPasswordResult').style.display = 'none';
  document.getElementById('resetPasswordValue').textContent = '';

  closeModal('adminUserModal');
  document.getElementById('resetPasswordModal').classList.add('show');
}

async function hamCapLaiMatKhau() {
  const ma_user     = document.getElementById('resetUserId').value;
  const mat_khau_moi = document.getElementById('resetPasswordInput').value.trim();

  if (!ma_user) { showToast('⚠️ Thiếu thông tin!'); return; }

  try {
    const res = await fetch('/api/cap-lai-mat-khau', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ ma_user: Number(ma_user), mat_khau_moi: mat_khau_moi })
    });
    const result = await res.json();

    if (!result.status) {
      showToast('❌ ' + result.message);
      return;
    }

    // Hiển thị mật khẩu ĐÚNG MỘT LẦN (không lưu biến toàn cục / localStorage)
    document.getElementById('resetPasswordValue').textContent = result.data.mat_khau_moi;
    document.getElementById('resetPasswordResult').style.display = 'block';
    showToast('✅ Đã cấp lại mật khẩu!');
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

function closeResetPasswordModal() {
  document.getElementById('resetPasswordInput').value = '';
  document.getElementById('resetPasswordValue').textContent = '';
  document.getElementById('resetPasswordResult').style.display = 'none';
  closeModal('resetPasswordModal');
}

// ─── QUẢN LÝ TÀI KHOẢN QUẢN LÝ ─ ĐÃ GỠ (017: không còn luồng thêm Quản lý trong UI) ────────

async function openProductDetail(productId) {
  const content = document.getElementById('productDetailContent');
  content.innerHTML = `<div style="text-align:center; padding:60px 0; color:var(--text-muted);">⏳ Đang tải...</div>`;
  document.getElementById('productDetailModal').classList.add('show');

  try {
    const res    = await fetch(`/api/products/${productId}`);
    const result = await res.json();

    if (!result.status) {
      content.innerHTML = `<div style="text-align:center; padding:60px 0; color:var(--red);">❌ Không tìm thấy sản phẩm!</div>`;
      return;
    }

    const p = result.data;
    const discountPercent = p.old_price
      ? Math.round((1 - p.price / p.old_price) * 100)
      : 0;

    content.innerHTML = `
      <div style="display:flex; gap:24px; flex-wrap:wrap;">

        <!-- Ảnh sản phẩm -->
        <div style="
            flex:0 0 220px;
            height:220px;
            background:var(--bg);
            border-radius:12px;
            overflow:hidden;
            position:relative;
        ">

          ${
            p.image_url
              ? `<img
                    src="/static/${p.image_url}"
                    alt="${p.name}"
                    style="
                      width:100%;
                      height:100%;
                      object-fit:contain;
                      padding:10px;
                    "
                >`
              : `<div style="
                    width:100%;
                    height:100%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:90px;
                ">
                  ${p.emoji || '📦'}
                </div>`
          }

          ${
            discountPercent > 0
              ? `<span style="
                    position:absolute;
                    top:10px;
                    left:10px;
                    background:var(--red);
                    color:white;
                    font-size:12px;
                    font-weight:700;
                    padding:3px 8px;
                    border-radius:6px;
                ">
                    -${discountPercent}%
                </span>`
              : ''
          }

        </div>

        <!-- Thông tin chính -->
        <div style="flex:1; min-width:240px;">
          <h2 style="margin:0 0 6px; font-size:20px;">${p.name}</h2>

          <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px; font-size:13px; color:var(--text-muted); flex-wrap:wrap;">
            <span>Đã bán ${p.sold || 0}</span>
            <span>·</span>
            <span>📁 ${p.category_name || '—'}</span>
          </div>

          <!-- Shop -->
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:14px;
                      padding:8px 12px; background:var(--bg); border-radius:8px; font-size:13px;">
            🏪 <b>${p.shop || 'Pobby Official'}</b>
          </div>

          <!-- Giá -->
          <div style="margin-bottom:16px;">
            ${p.old_price ? `
              <div style="font-size:14px; color:var(--text-muted); text-decoration:line-through;">
                ${Number(p.old_price).toLocaleString('vi-VN')}đ
              </div>` : ''}
            <div style="font-size:26px; font-weight:800; color:var(--red);">
              ${Number(p.price).toLocaleString('vi-VN')}đ
            </div>
          </div>

          <!-- Tồn kho -->
          <div style="font-size:13px; color:${p.quantity <= 5 ? 'var(--red)' : 'var(--text-secondary)'}; margin-bottom:16px;">
            ${p.quantity > 0
              ? `📦 Còn lại: <b>${p.quantity}</b> sản phẩm`
              : `❌ Hết hàng`}
          </div>

          <!-- Số lượng mua + nút giỏ hàng -->
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="display:flex; align-items:center; border:1px solid var(--border); border-radius:8px;">
              <button onclick="changeDetailQty(-1)"
                style="width:34px; height:34px; border:none; background:none; cursor:pointer; font-size:18px;">−</button>
              <input id="detailQtyInput" type="number" value="1" min="1" max="${p.quantity || 1}"
                style="width:44px; text-align:center; border:none; outline:none; font-weight:700;">
              <button onclick="changeDetailQty(1)"
                style="width:34px; height:34px; border:none; background:none; cursor:pointer; font-size:18px;">+</button>
            </div>
            <button onclick="addToCartFromDetail(${p.id}, ${p.price}, ${p.quantity || 0})"
              class="checkout-btn" style="flex:1; ${p.quantity <= 0 ? 'opacity:0.5; pointer-events:none;' : ''}">
              ${p.quantity > 0 ? '🛒 Thêm vào giỏ hàng' : 'Hết hàng'}
            </button>
          </div>
        </div>
      </div>

      <!-- Mô tả sản phẩm -->
      <div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--border);">
        <h3 style="margin-bottom:10px; font-size:16px;">📝 Mô tả sản phẩm</h3>
        <div style="font-size:14px; line-height:1.7; color:var(--text-secondary); white-space:pre-line;">
          ${p.description ? p.description : 'Người bán chưa cập nhật mô tả cho sản phẩm này.'}
        </div>
      </div>
    `;

  } catch (e) {
    content.innerHTML = `<div style="text-align:center; padding:60px 0; color:var(--red);">❌ Lỗi tải dữ liệu sản phẩm!</div>`;
    console.error('Lỗi openProductDetail:', e);
  }
}

// Tăng/giảm số lượng trong modal chi tiết
function changeDetailQty(delta) {
  const input = document.getElementById('detailQtyInput');
  const max   = parseInt(input.max) || 999;
  let value   = parseInt(input.value) || 1;
  value = Math.min(max, Math.max(1, value + delta));
  input.value = value;
}

// Thêm vào giỏ từ trang chi tiết — lấy đúng số lượng người dùng chọn
function addToCartFromDetail(productId, price, maxQty) {
  if (maxQty <= 0) {
    showToast('⚠️ Sản phẩm đã hết hàng!');
    return;
  }
  const qty = parseInt(document.getElementById('detailQtyInput').value) || 1;
  addToCart(productId, qty, price);
  closeModal('productDetailModal');
}
function clearUserFilters() {
  document.querySelectorAll('#filterCatList input[type="checkbox"]').forEach(cb => cb.checked = false);
  document.getElementById('userSearchInput').value = '';
  document.getElementById('priceMin').value = '';
  document.getElementById('priceMax').value = '';

document.getElementById('priceMin').dataset.rawValue = '';
document.getElementById('priceMax').dataset.rawValue = '';
  document.getElementById('chkInStock').checked = false;
  document.getElementById('chkOnSale').checked = false;
  document.getElementById('searchCategorySelect').value = 'all';
  document.getElementById('sortSelect').value = 'default';
  applyUserFilters();
}
// ── DEBOUNCE: tránh gọi filter liên tục khi đang gõ ─────────
let priceDebounceTimer = null;

function onPriceInput() {
  clearTimeout(priceDebounceTimer);
  priceDebounceTimer = setTimeout(() => {
    formatPriceInputs();
    applyUserFilters();
  }, 400); // chờ 400ms sau khi ngừng gõ mới filter
}

// Format hiển thị số có dấu phẩy, nhưng vẫn lưu số thật để filter
function formatPriceInputs() {
  ['priceMin', 'priceMax'].forEach(id => {
    const input = document.getElementById(id);
    if (!input) return;

    // Lấy chỉ các chữ số
    const raw = input.value.replace(/\D/g, '');
    if (!raw) { input.value = ''; return; }

    // Format: 19900000 → "19,900,000"
    input.value = Number(raw).toLocaleString('vi-VN');
    // Lưu giá trị thô vào dataset để applyUserFilters đọc
    input.dataset.rawValue = raw;
  });
}
// KHỞI CHẠY GIAO DIỆN MẶC ĐỊNH
loadCategories();
loadProducts();
khoiPhucDangNhap();

// ============================================================
// 004 SELLER — GHI DE SELLER DUNG /api/seller/* (store tu session)
// Hien thi message server + textContent chong XSS (2 lop voi BUS).
// ============================================================
async function renderSellerProducts() {
  const tbody = document.getElementById('tblSellerProductsBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Đang tải...</td></tr>';
  try {
    const res = await fetch('/api/seller/san-pham');
    const result = await res.json();
    if (!result.status) {
      tbody.innerHTML = '';
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 6;
      td.style.textAlign = 'center';
      td.textContent = result.message || 'Không tải được sản phẩm!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      if (res.status === 403) showToast('❌ ' + (result.message || 'Không có quyền!'));
      return;
    }
    if (!result.data.length) {
      tbody.innerHTML = '';
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 6;
      td.style.textAlign = 'center';
      td.textContent = 'Chưa có sản phẩm nào. Hãy thêm sản phẩm đầu tiên!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    // 013: bộ lọc — ton kho + tu khoa ten, loc client truoc khi vẽ bảng
    const locTonKho = document.getElementById('spFilterStock')?.value || 'all';
    const locTuKhoa = (document.getElementById('spSearchFilter')?.value || '').trim().toLowerCase();
    let listLoc = result.data;
    if (locTonKho !== 'all') {
      listLoc = listLoc.filter(p => {
        const soLuong = Number(p.quantity || 0);
        if (locTonKho === 'in-stock') return soLuong > 5;
        if (locTonKho === 'low-stock') return soLuong >= 1 && soLuong <= 5;
        if (locTonKho === 'out-of-stock') return soLuong === 0;
        return true;
      });
    }
    if (locTuKhoa) listLoc = listLoc.filter(p => (p.name || '').toLowerCase().includes(locTuKhoa));
    if (!listLoc.length) {
      tbody.innerHTML = '';
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 6;
      td.style.textAlign = 'center';
      td.textContent = 'Không tìm thấy kết quả';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    tbody.innerHTML = '';
    listLoc.forEach((p) => {
      const tr = document.createElement('tr');
      const tdAnh = document.createElement('td');
      tdAnh.style.textAlign = 'center';
      if (p.image_url) {
        const img = document.createElement('img');
        img.src = '/static/' + p.image_url;
        img.alt = p.name || '';
        img.style.cssText = 'width:60px;height:60px;object-fit:cover;border-radius:8px;border:1px solid #ddd;';
        tdAnh.appendChild(img);
      } else {
        const sp = document.createElement('span');
        sp.style.fontSize = '28px';
        sp.textContent = p.emoji || '📦';
        tdAnh.appendChild(sp);
      }
      tr.appendChild(tdAnh);
      const tdTen = document.createElement('td');
      const bTen = document.createElement('div');
      bTen.style.fontWeight = '600';
      bTen.textContent = p.name || '';
      const dCat = document.createElement('div');
      dCat.style.cssText = 'font-size:11px;color:var(--text-muted);';
      dCat.textContent = p.category_name || '';
      tdTen.appendChild(bTen);
      tdTen.appendChild(dCat);
      tr.appendChild(tdTen);
      const tdGia = document.createElement('td');
      tdGia.style.cssText = 'color:var(--red);font-weight:700;';
      tdGia.textContent = Number(p.price || 0).toLocaleString('vi-VN') + 'đ';
      tr.appendChild(tdGia);
      const tdSl = document.createElement('td');
      tdSl.style.textAlign = 'center';
      tdSl.textContent = p.quantity || 0;
      tr.appendChild(tdSl);
      // 015 FR-024: cột Trạng thái = pill 4 mức (dùng class sẵn có + 1 class mới .status-hidden)
      const tdTrang = document.createElement('td');
      tdTrang.style.textAlign = 'center';
      const pillTrang = document.createElement('span');
      let clsTrang = 'user-status-active', textTrang = 'Đang bán';
      if (!Number(p.is_active)) {
        clsTrang = 'status-hidden'; textTrang = 'Đang ẩn';
      } else if (Number(p.quantity || 0) === 0) {
        clsTrang = 'status-cancelled'; textTrang = 'Hết hàng';
      } else if (Number(p.quantity || 0) >= 1 && Number(p.quantity || 0) <= 5) {
        clsTrang = 'status-pending'; textTrang = 'Sắp hết';
      }
      pillTrang.className = 'badge-status ' + clsTrang;
      pillTrang.textContent = textTrang;
      const tDaBan = document.createElement('div');  // FR-025: số đã bán nằm dưới pill
      tDaBan.style.cssText = 'font-size:10px;color:var(--text-muted);margin-top:4px;';
      tDaBan.textContent = 'Đã bán: ' + (p.sold || 0);
      tdTrang.appendChild(pillTrang);
      tdTrang.appendChild(tDaBan);
      tr.appendChild(tdTrang);
      const tdCn = document.createElement('td');
      const btnSua = document.createElement('button');
      btnSua.className = 'admin-action-btn btn-edit';
      btnSua.textContent = '✏️ Sửa';
      btnSua.onclick = () => openEditSellerProduct(p.id);
      const btnAnHien = document.createElement('button');
      btnAnHien.className = 'admin-action-btn btn-edit';
      btnAnHien.textContent = p.is_active ? '🙈 Ẩn' : '👁️ Hiện';
      btnAnHien.onclick = () => sellerAnHien(p.id, p.is_active ? 0 : 1);
      [btnSua, btnAnHien].forEach((b) => tdCn.appendChild(b));
      tr.appendChild(tdCn);
      tbody.appendChild(tr);
    });
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function openEditSellerProduct(productId) {
  try {
    const res = await fetch('/api/seller/san-pham');
    const result = await res.json();
    if (!result.status) { showToast('❌ ' + (result.message || 'Không tải được!')); return; }
    const p = (result.data || []).find((x) => x.id === productId);
    if (!p) { showToast('❌ Không có quyền thao tác trên sản phẩm này!'); return; }
    document.getElementById('adminProductModalTitle').textContent = '✏️ Chỉnh sửa sản phẩm';
    document.getElementById('editProductId').value = p.id;
    document.getElementById('editProductId').dataset.sellerMode = 'true';
    document.getElementById('prodName').value = p.name || '';
    document.getElementById('prodPrice').value = p.price || '';
    document.getElementById('prodOldPrice').value = p.old_price || '';
    document.getElementById('prodStock').value = p.quantity || 0;
    document.getElementById('prodEmoji').value = p.emoji || '';
    document.getElementById('prodDesc').value = p.description || '';
    await loadCategoriesForProductModal(p.category_name);
    document.getElementById('adminProductModal').classList.add('show');
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function sellerAnHien(productId, isActive) {
  try {
    const res = await fetch(`/api/seller/san-pham/${productId}/an-hien`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: isActive })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) renderSellerProducts();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// 015 FR-016/017: tab Quản lý nhập hàng — bảng + nút nhập theo từng dòng
async function renderSellerNhapHang() {
  const tbody = document.getElementById('spNhapHangBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Đang tải...</td></tr>';
  try {
    const res = await fetch('/api/seller/san-pham');
    const result = await res.json();
    if (!result.status || !Array.isArray(result.data)) {
      tbody.innerHTML = '';
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.style.textAlign = 'center';
      td.textContent = result.message || 'Không tải được sản phẩm!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    const locTuKhoa = (document.getElementById('nhSearchFilter')?.value || '').trim().toLowerCase();
    const locTon = document.getElementById('nhFilterStock')?.value || 'all';
    let listLoc = result.data;
    if (locTuKhoa) listLoc = listLoc.filter(p => (p.name || '').toLowerCase().includes(locTuKhoa));
    if (locTon !== 'all') {
      listLoc = listLoc.filter(p => {
        const so = Number(p.quantity || 0);
        if (locTon === 'low-stock') return so >= 1 && so <= 5;
        if (locTon === 'out-of-stock') return so === 0;
        return so > 5;
      });
    }
    tbody.innerHTML = '';
    if (!listLoc.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.style.textAlign = 'center';
      td.textContent = 'Không tìm thấy kết quả';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    listLoc.forEach((p) => {
      const tr = document.createElement('tr');
      const tdTen = document.createElement('td');
      const bTen = document.createElement('div');
      bTen.style.fontWeight = '600';
      bTen.textContent = (p.emoji || '📦') + ' ' + (p.name || '');
      const dCat = document.createElement('div');
      dCat.style.cssText = 'font-size:11px;color:var(--text-muted);';
      dCat.textContent = p.category_name || '';
      tdTen.appendChild(bTen);
      tdTen.appendChild(dCat);
      tr.appendChild(tdTen);
      const tdTon = document.createElement('td');
      tdTon.style.textAlign = 'center';
      tdTon.style.fontWeight = '700';
      tdTon.textContent = String(Number(p.quantity || 0).toLocaleString('vi-VN'));
      tr.appendChild(tdTon);
      const tdNhap = document.createElement('td');
      const inp = document.createElement('input');
      inp.type = 'number';
      inp.id = 'nhQty' + p.id;
      inp.min = '1';
      inp.step = '1';
      inp.value = '10';
      inp.style.cssText = 'width:80px;padding:6px;border:1px solid var(--border);border-radius:6px;';
      tdNhap.appendChild(inp);
      tr.appendChild(tdNhap);
      const tdTrang = document.createElement('td');
      tdTrang.style.textAlign = 'center';
      const pill = document.createElement('span');
      if (!Number(p.is_active)) {
        pill.className = 'badge-status status-hidden';
        pill.textContent = 'Đang ẩn';
      } else if (Number(p.quantity || 0) === 0) {
        pill.className = 'badge-status status-cancelled';
        pill.textContent = 'Hết hàng';
      } else if (Number(p.quantity || 0) >= 1 && Number(p.quantity || 0) <= 5) {
        pill.className = 'badge-status status-pending';
        pill.textContent = 'Sắp hết';
      } else {
        pill.className = 'badge-status user-status-active';
        pill.textContent = 'Đang bán';
      }
      tdTrang.appendChild(pill);
      tr.appendChild(tdTrang);
      const tdBt = document.createElement('td');
      const btn = document.createElement('button');
      btn.className = 'admin-action-btn btn-confirm';
      btn.textContent = '📥 Nhập hàng';
      btn.onclick = () => nhapHangSeller(p.id, 'nhQty' + p.id);
      tdBt.appendChild(btn);
      tr.appendChild(tdBt);
      tbody.appendChild(tr);
    });
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// 015 FR-018/019: gửi số lượng nhập — kiểm tra định dạng trước khi gọi API
async function nhapHangSeller(productId, inputId) {
  const raw = (document.getElementById(inputId)?.value || '').trim();
  if (!/^\d+$/.test(raw) || Number(raw) <= 0) {
    showToast('⚠️ Số lượng nhập phải là số nguyên lớn hơn 0!');
    return;
  }
  try {
    const res = await fetch(`/api/seller/san-pham/${productId}/nhap-hang`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ so_luong: Number(raw) })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) renderSellerNhapHang();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// Ghi de luu/xoa seller dung endpoint co gate (004)
const _handleSaveProductGoc = handleSaveProduct;
handleSaveProduct = async function (e) {
  e.preventDefault();
  const isSellerMode = document.getElementById('editProductId').dataset.sellerMode === 'true';
  if (!isSellerMode) return _handleSaveProductGoc(e);
  const productId = document.getElementById('editProductId').value;
  const isEdit = !!productId;
  const payload = {
    name: document.getElementById('prodName').value.trim(),
    price: document.getElementById('prodPrice').value,
    old_price: document.getElementById('prodOldPrice').value || null,
    quantity: document.getElementById('prodStock').value,
    emoji: document.getElementById('prodEmoji').value.trim(),
    description: document.getElementById('prodDesc').value.trim(),
    category_id: document.getElementById('prodCategory').value
  };
  if (!payload.name) { showToast('⚠️ Tên sản phẩm không được trống!'); return; }
  try {
    const url = isEdit
      ? `/api/seller/san-pham/${productId}`
      : '/api/seller/san-pham';
    const res = await fetch(url, {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) {
      closeModal('adminProductModal');
      renderSellerProducts();
      loadProducts();
    }
  } catch (err) {
    showToast('❌ Lỗi kết nối!');
  }
};

// ============================================================
// 015 FR-026/027/028 — DON HANG SELLER dung /api/seller/don-hang (co gate)
// ============================================================
renderSellerOrders = async function () {
  const tbody = document.getElementById('tblSellerOrdersBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">Đang tải...</td></tr>';
  try {
    const res = await fetch('/api/seller/don-hang');
    const result = await res.json();
    tbody.innerHTML = '';
    if (!result.status) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 8;
      td.style.textAlign = 'center';
      td.textContent = result.message || 'Không tải được đơn hàng!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    if (!result.data.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 8;
      td.style.textAlign = 'center';
      td.textContent = 'Chưa có đơn hàng nào cho gian hàng này';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    // 013: bộ lọc — trang thai don, loc client truoc khi vẽ bảng
    const locStatus = document.getElementById('soFilterStatus')?.value || 'all';
    let listLoc = result.data;
    if (locStatus !== 'all') listLoc = listLoc.filter(o => o.Status === locStatus);
    if (!listLoc.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 8;
      td.style.textAlign = 'center';
      td.textContent = 'Không tìm thấy kết quả';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    const nhanTrangThai = {
      Pending: 'Chờ duyệt', Confirmed: 'Đã xác nhận', Shipping: 'Đang giao',
      Completed: 'Hoàn thành', Cancelled: 'Đã hủy'
    };
    const nutTiepTheo = { Pending: 'Confirmed', Confirmed: 'Shipping', Shipping: 'Completed' };
    const nhanNut = { Confirmed: '✅ Xác nhận', Shipping: '🚚 Giao hàng', Completed: '🏁 Hoàn thành' };
    // 015 FR-028: pill trạng thái dùng class badge-status sẵn có
    const clsTrangThai = {
      Pending: 'status-pending', Confirmed: 'status-confirmed', Shipping: 'status-shipping',
      Completed: 'status-done', Cancelled: 'status-cancelled'
    };
    listLoc.forEach((o) => {
      const tr = document.createElement('tr');
      const tdId = document.createElement('td');
      tdId.style.fontWeight = '700';
      tdId.textContent = '#' + o.OrderId;
      tr.appendChild(tdId);
      const tdKh = document.createElement('td');
      const dTen = document.createElement('div');
      dTen.style.fontWeight = '600';
      dTen.textContent = o.ReceiverName || '';
      const dPhone = document.createElement('div');
      dPhone.style.fontSize = '11px';
      dPhone.textContent = '📞 ' + (o.ReceiverPhone || '');
      tdKh.appendChild(dTen);
      tdKh.appendChild(dPhone);
      tr.appendChild(tdKh);
      const tdSp = document.createElement('td');   // 015 FR-027: tóm tắt mặt hàng shop này
      const dsItem = (o.Items || []).slice(0, 3);
      dsItem.forEach((it) => {
        const dSp = document.createElement('div');
        dSp.style.fontSize = '12px';
        dSp.textContent = (it.Emoji || '') + ' ' + (it.ProductName || '') + ' x' + (it.Quantity || 0);
        tdSp.appendChild(dSp);
      });
      if ((o.Items || []).length > 3) {
        const dThem = document.createElement('div');
        dThem.style.cssText = 'font-size:11px;color:var(--text-muted);';
        dThem.textContent = '…+' + String((o.Items || []).length - 3) + ' sản phẩm nữa';
        tdSp.appendChild(dThem);
      }
      if (!(o.Items || []).length) tdSp.textContent = '—';
      tr.appendChild(tdSp);
      const tdTien = document.createElement('td');
      tdTien.style.fontWeight = '700';
      tdTien.textContent = Number(o.TotalAmount || 0).toLocaleString('vi-VN') + 'đ';
      tr.appendChild(tdTien);
      const tdTt = document.createElement('td');   // pill trạng thái
      const pillTt = document.createElement('span');
      pillTt.className = 'badge-status ' + (clsTrangThai[o.Status] || 'status-pending');
      pillTt.textContent = nhanTrangThai[o.Status] || o.Status;
      tdTt.appendChild(pillTt);
      tr.appendChild(tdTt);
      const tdNgay = document.createElement('td');
      tdNgay.style.fontSize = '12px';
      tdNgay.textContent = o.CreatedAt || '—';
      tr.appendChild(tdNgay);
      const tdCt = document.createElement('td');   // 015 FR-026: Xem chi tiết đơn hàng
      const btnCt = document.createElement('button');
      btnCt.className = 'admin-action-btn btn-edit';
      btnCt.textContent = '🔍 Xem chi tiết đơn hàng';
      btnCt.onclick = () => showChiTietDonHang(o);
      tdCt.appendChild(btnCt);
      tr.appendChild(tdCt);
      const tdCn = document.createElement('td');
      const tiep = nutTiepTheo[o.Status];
      if (tiep) {
        const btn = document.createElement('button');
        btn.className = 'admin-action-btn btn-confirm';
        btn.textContent = nhanNut[tiep];
        btn.onclick = () => sellerCapNhatDon(o.OrderId, tiep);
        tdCn.appendChild(btn);
      }
      if (o.Status === 'Pending' || o.Status === 'Confirmed' || o.Status === 'Shipping') {
        const btnHuy = document.createElement('button');
        btnHuy.textContent = '✖ Hủy';
        btnHuy.onclick = () => sellerCapNhatDon(o.OrderId, 'Cancelled');
        tdCn.appendChild(btnHuy);
      }
      if (!tdCn.childNodes.length) tdCn.textContent = '—';
      tr.appendChild(tdCn);
      tbody.appendChild(tr);
    });
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
};

sellerCapNhatDon = async function (orderId, newStatus) {
  if (!confirm(`Cập nhật đơn #${orderId} sang ${newStatus}?`)) return;
  try {
    const res = await fetch(`/api/seller/don-hang/${orderId}/trang-thai`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) renderSellerOrders();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
};

// 015 FR-026/028: modal chi tiết đơn hàng — nội dung dùng textContent (chống XSS)
function showChiTietDonHang(o) {
  const modal = document.getElementById('sellerOrderDetailModal');
  if (!modal) return;
  const content = document.getElementById('sellerOrderDetailContent');
  if (!content) return;
  content.innerHTML = '';
  const fmtTien = (n) => Number(n || 0).toLocaleString('vi-VN') + 'đ';
  const nhanTT = { Pending: 'Chờ duyệt', Confirmed: 'Đã xác nhận', Shipping: 'Đang giao',
                   Completed: 'Hoàn thành', Cancelled: 'Đã hủy' };
  const hang = (nhan, giaTri) => {
    const dong = document.createElement('div');
    dong.style.cssText = 'display:flex;justify-content:space-between;gap:16px;'
      + 'padding:7px 0;border-bottom:1px solid var(--border);font-size:13px;';
    const lb = document.createElement('div');
    lb.textContent = nhan;
    lb.style.color = 'var(--text-muted)';
    const vl = document.createElement('div');
    vl.textContent = giaTri;
    vl.style.cssText = 'font-weight:600;text-align:right;';
    dong.appendChild(lb);
    dong.appendChild(vl);
    content.appendChild(dong);
  };
  hang('Mã đơn', '#' + String(o.OrderId || ''));
  hang('Ngày đặt', String(o.CreatedAt || '—'));
  hang('Trạng thái', nhanTT[o.Status] || String(o.Status || '—'));
  hang('Người nhận', String(o.ReceiverName || '—'));
  hang('SĐT', String(o.ReceiverPhone || '—'));
  hang('Địa chỉ giao', String(o.ShippingAddress || '—'));
  hang('Thanh toán', String(o.PaymentMethod || '—'));
  const tieuDeSp = document.createElement('div');
  tieuDeSp.textContent = 'Mặt hàng trong đơn (của shop bạn)';
  tieuDeSp.style.cssText = 'font-weight:700;font-size:13px;color:var(--text-muted);padding:8px 0;';
  content.appendChild(tieuDeSp);
  const dsSp = document.createElement('div');
  if ((o.Items || []).length) {
    (o.Items || []).forEach((it) => {
      const dSp = document.createElement('div');
      dSp.style.cssText = 'font-size:13px;padding:5px 0;border-bottom:1px solid var(--border);';
      dSp.textContent = (it.Emoji || '') + ' ' + (it.ProductName || '—') + ' x' + (it.Quantity || 0)
        + ' × ' + fmtTien(it.UnitPrice) + ' = ' + fmtTien(it.TotalPrice);
      dsSp.appendChild(dSp);
    });
  } else {
    dsSp.textContent = '—';
  }
  content.appendChild(dsSp);
  hang('Tạm tính', fmtTien(o.SubTotal));
  hang('Chiết khấu', fmtTien(o.DiscountAmount));
  hang('Phí giao hàng', fmtTien(o.ShippingFee));
  hang('Tổng cộng', fmtTien(o.TotalAmount));
  hang('Ghi chú', String(o.Note || '—'));
  modal.classList.add('show');
}

// ============================================================
// 015 FR-029/030/031/032 — TONG QUAN GIAN HANG (endpoint co gate)
// Dung .admin-card + .stats-grid/.stat-box/.stat-val + .empty-state.
// ============================================================
renderSellerOverview = async function () {
  const container = document.getElementById('sellerOverviewContent');
  if (!container) return;
  container.innerHTML = '';
  const dangTai = document.createElement('div');
  dangTai.style.textAlign = 'center';
  dangTai.textContent = 'Đang tải thống kê...';
  container.appendChild(dangTai);
  try {
    const [rSp, rTk] = await Promise.all([
      fetch('/api/seller/san-pham'),
      fetch('/api/seller/thong-ke/tong-quan')
    ]);
    const reSp = await rSp.json();
    const tk = await rTk.json();
    container.innerHTML = '';
    if (!reSp.status || !Array.isArray(reSp.data)) {
      const khong = document.createElement('div');
      khong.className = 'empty-state';
      const p = document.createElement('p');
      p.textContent = reSp.message || 'Chưa có dữ liệu';
      khong.appendChild(p);
      container.appendChild(khong);
      return;
    }
    const d = tk.data || {};
    const dsSanPham = reSp.data;
    const tongSanPham = reSp.data.length;      // tổng sản phẩm của shop (FR-030)
    // Điều kiện sắp hết hàng: quantity >= 1 && quantity <= 5 (chỉ còn 1–5 cái)
    const sapHet = dsSanPham.filter(p => Number(p.quantity || 0) >= 1 && Number(p.quantity || 0) <= 5);
    const hetHang = dsSanPham.filter(p => Number(p.quantity || 0) === 0);
    const tongDaBan = dsSanPham.reduce((t, p) => t + (Number(p.sold || 0)), 0);
    if (!tongSanPham) {
      const khong = document.createElement('div');
      khong.className = 'empty-state';
      const p = document.createElement('p');
      p.textContent = 'Chưa có sản phẩm nào. Hãy thêm sản phẩm đầu tiên!';
      khong.appendChild(p);
      container.appendChild(khong);
      return;
    }
    const shop = currentUser?.store || {};
    const cardThuong = (title, phu) => {
      const card = document.createElement('div');
      card.className = 'admin-card';
      const hd = document.createElement('div');
      hd.style.cssText = 'display:flex;justify-content:space-between;align-items:center;';
      const t = document.createElement('h3');
      t.textContent = title;
      hd.appendChild(t);
      if (phu) hd.appendChild(phu);
      card.appendChild(hd);
      return card;
    };
    const pillHoatDong = document.createElement('span');  // 015 FR-029: shop Đang hoạt động
    pillHoatDong.className = 'user-status-active';
    pillHoatDong.textContent = 'Đang hoạt động';
    const cardShop = cardThuong('🏪 ' + (shop.store_name || 'Gian hàng của tôi'), pillHoatDong);
    const moTa = document.createElement('p');
    moTa.style.cssText = 'font-size:13px;color:var(--text-muted);margin:6px 0 0;';
    moTa.textContent = (shop.description || '') || '—';
    cardShop.appendChild(moTa);
    container.appendChild(cardShop);
    const cardThongKe = document.createElement('div');
    cardThongKe.className = 'admin-card';
    const grid = document.createElement('div');
    grid.className = 'stats-grid';
    const motBox = (nhan, giaTri, phu) => {
      const box = document.createElement('div');
      box.className = 'stat-box';
      const lb = document.createElement('div');
      lb.textContent = nhan;
      const val = document.createElement('div');
      val.className = 'stat-val';
      val.textContent = giaTri;
      box.appendChild(lb);
      box.appendChild(val);
      if (phu) {
        const ph = document.createElement('div');
        ph.style.cssText = 'font-size:11px;color:var(--text-muted);';
        ph.textContent = phu;
        box.appendChild(ph);
      }
      grid.appendChild(box);
    };
    motBox('Tổng sản phẩm', String(tongSanPham), 'đang bày bán');
    motBox('Sắp hết hàng', String(sapHet.length), 'còn 1–5 cái');
    motBox('Hết hàng', String(hetHang.length), 'cần nhập thêm');
    motBox('Tổng đã bán', String(tongDaBan), 'sản phẩm');
    cardThongKe.appendChild(grid);
    container.appendChild(cardThongKe);
    const cardDoanhThu = document.createElement('div');
    cardDoanhThu.className = 'admin-card';
    const hDoanhThu = document.createElement('h3');
    hDoanhThu.textContent = '💰 Doanh thu ước tính';
    cardDoanhThu.appendChild(hDoanhThu);
    const dThu = document.createElement('div');
    dThu.className = 'stat-val';
    dThu.textContent = 'Đã bán: ' + Number(d.doanh_thu || 0).toLocaleString('vi-VN') + 'đ';
    cardDoanhThu.appendChild(dThu);
    const dDon = document.createElement('p');
    dDon.style.cssText = 'font-size:13px;color:var(--text-muted);margin:4px 0 0;';
    dDon.textContent = String(d.tong_don || 0) + ' đơn · ' + String(d.cho_duyet || 0)
      + ' chờ duyệt · ' + String(d.dang_giao || 0) + ' đang giao · '
      + String(d.hoan_thanh || 0) + ' hoàn thành · ' + String(d.da_huy || 0) + ' đã hủy';
    cardDoanhThu.appendChild(dDon);
    container.appendChild(cardDoanhThu);
    const cardTopSp = document.createElement('div');
    cardTopSp.className = 'admin-card';
    if ((d.top_san_pham || []).length) {
      const hTop = document.createElement('h3');
      hTop.textContent = '🔥 Top sản phẩm bán chạy';
      cardTopSp.appendChild(hTop);
      (d.top_san_pham || []).forEach((tp) => {
        const dong = document.createElement('div');
        dong.style.cssText = 'display:flex;justify-content:space-between;padding:6px 0;'
          + 'border-bottom:1px solid var(--border);font-size:13px;';
        const ten = document.createElement('div');
        ten.textContent = String(tp.ProductName || tp.ten || '—');
        const sl = document.createElement('div');
        sl.textContent = 'Đã bán: ' + String(tp.TotalQuantity || tp.sold || 0);
        sl.style.cssText = 'font-weight:600;color:var(--text-muted);';
        dong.appendChild(ten);
        dong.appendChild(sl);
        cardTopSp.appendChild(dong);
      });
    }
    // container.appendChild(cardTopSp);
  } catch (e) {
    const loi = document.createElement('div');
    loi.className = 'empty-state';
    const p = document.createElement('p');
    p.textContent = '❌ Lỗi tải dữ liệu!';
    loi.appendChild(p);
    container.appendChild(loi);
  }
};

// 010 US2 — TRANG SHOP (tách khỏi Tổng quan): đọc shop về điền vào form spane-shop
async function renderTrangShop() {
  const inputTen = document.getElementById('sellerShopName');
  if (!inputTen) return;
  try {
    const res    = await fetch('/api/seller/trang-shop');
    const result = await res.json();
    if (!result.status) {
      showToast('❌ ' + (result.message || 'Không tải được thông tin shop!'));
      return;
    }
    document.getElementById('sellerShopName').value = result.data.store_name || '';
    document.getElementById('sellerShopDesc').value = result.data.description || '';
    const tn = result.data.tham_nien;
    document.getElementById('sellerShopThamNien').value =
      (tn === null || tn === undefined) ? '' : tn;
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function sellerLuuTrangShop() {
  const payload = {
    ten_shop: document.getElementById('sellerShopName').value,
    gioi_thieu: document.getElementById('sellerShopDesc').value,
    tham_nien: document.getElementById('sellerShopThamNien').value === ''
      ? null
      : Number(document.getElementById('sellerShopThamNien').value)
  };
  try {
    const res = await fetch('/api/seller/trang-shop', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) renderTrangShop();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ============================================================
// 010 US3 — QUẢN LÝ GIÁ BÁN (tách khỏi Sản phẩm): bảng giá spane-gia
// ============================================================
async function renderGiaBan() {
  const tbody = document.getElementById('tblSellerGiaBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Đang tải...</td></tr>';
  try {
    const res    = await fetch('/api/seller/san-pham');
    const result = await res.json();
    tbody.innerHTML = '';
    if (!result.status) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.style.textAlign = 'center';
      td.textContent = result.message || 'Không tải được sản phẩm!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    if (!result.data.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.style.textAlign = 'center';
      td.textContent = 'Chưa có sản phẩm nào. Hãy thêm sản phẩm trước!';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    result.data.forEach((p) => {
      const tr = document.createElement('tr');
      const tdTen = document.createElement('td');
      const bTen = document.createElement('div');
      bTen.style.fontWeight = '600';
      bTen.textContent = p.name || '';
      const dCat = document.createElement('div');
      dCat.style.cssText = 'font-size:11px;color:var(--text-muted);';
      dCat.textContent = p.category_name || '';
      tdTen.appendChild(bTen);
      tdTen.appendChild(dCat);
      tr.appendChild(tdTen);
      const tdGiaCu = document.createElement('td');
      tdGiaCu.style.cssText = 'color:var(--red);font-weight:700;';
      tdGiaCu.textContent = Number(p.price || 0).toLocaleString('vi-VN') + 'đ';
      tr.appendChild(tdGiaCu);
      const tdGiaMoi = document.createElement('td');
      const inp = document.createElement('input');
      inp.type = 'number';
      inp.min = '1';
      inp.id = 'giaMoi-' + p.id;
      inp.value = p.price || '';
      inp.style.cssText = 'width:140px; padding:6px 8px; border:1px solid var(--border); border-radius:6px;';
      tdGiaMoi.appendChild(inp);
      tr.appendChild(tdGiaMoi);
      const tdSl = document.createElement('td');
      tdSl.style.textAlign = 'center';
      tdSl.textContent = p.quantity || 0;
      tr.appendChild(tdSl);
      const tdCn = document.createElement('td');
      const btn = document.createElement('button');
      btn.className = 'admin-action-btn btn-edit';
      btn.textContent = '💾 Lưu giá';
      btn.onclick = () => sellerDoiGia(p.id);
      tdCn.appendChild(btn);
      tr.appendChild(tdCn);
      tbody.appendChild(tr);
    });
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

async function sellerDoiGia(productId) {
  const inp = document.getElementById('giaMoi-' + productId);
  if (!inp) return;
  const giaMoi = Number(inp.value);
  if (!giaMoi || giaMoi <= 0) {
    showToast('⚠️ Giá bán mới phải lớn hơn 0!');
    return;
  }
  try {
    const res = await fetch('/api/seller/san-pham/' + productId + '/gia', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gia_moi: giaMoi })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + (result.message || ''));
    if (result.status) renderGiaBan();
  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}