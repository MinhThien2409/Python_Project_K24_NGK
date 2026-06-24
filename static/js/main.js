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
let currentVoucherDiscount = 0; // biến lưu giảm giá voucher

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

    // ✅ Kiểm tra lại trạng thái tài khoản với server (phòng trường hợp đã bị khóa)
    const res    = await fetch('http://localhost:5000/api/users');
    const result = await res.json();
    if (result.status) {
      const userMoi = result.data.find(u => u.ma_user === currentUser.ma_user);
      if (userMoi && userMoi.trang_thai === 'banned') {
        showToast('🔒 Tài khoản của bạn đã bị khóa!');
        xoaDangNhap();
        currentUser = null;
        return;
      }
    }

    updateHeaderForUser();
    await loadCartFromServer();

    const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;

    if (maQuyen === 20) {
      switchViewMode('admin');
    } else if (maQuyen === 13) {
      await loadSellerStore();
      switchViewMode('user');
    } else {
      switchViewMode('user');
    }

  } catch (e) {
    console.error('Lỗi khôi phục đăng nhập:', e);
    xoaDangNhap();
    currentUser = null;
  }
}

// ==========================================
// 1. CHUYỂN ĐỔI VIEW & ĐIỀU HƯỚNG
// ==========================================
function switchViewMode(mode) {
  document.getElementById('userInterface').style.display   = (mode === 'user')   ? 'block' : 'none';
  document.getElementById('adminInterface').style.display  = (mode === 'admin')  ? 'block' : 'none';
  document.getElementById('sellerDashboard').style.display = (mode === 'seller') ? 'block' : 'none';

  document.querySelectorAll('.view-switcher button').forEach(btn => btn.classList.remove('active'));

  if (mode === 'user') {
    const btn = document.getElementById('btnViewUser');
    if (btn) btn.classList.add('active');
  }
  else if (mode === 'admin') {
    const btn = document.getElementById('btnViewAdmin');
    if (btn) btn.classList.add('active');
       if (currentUser) loadAndApplyAdminPermissions(currentUser.ma_user);
  }
  else if (mode === 'seller') {
    const btn = document.getElementById('btnViewSeller');
    if (btn) btn.classList.add('active');
    switchSellerTab('overview');
  }
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
    await renderSellerOverview();  // ← Thay dòng cũ bằng dòng này
}
    else if (tabName === 'products') {
       await renderSellerProducts();

  } else if (tabName === 'orders') {
      await renderSellerOrders();
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
    const res    = await fetch(`http://localhost:5000/api/don-hang/cua-seller/${storeId}`);
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
    const res    = await fetch(`http://localhost:5000/api/don-hang/${orderId}/trang-thai`, {
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
    const res    = await fetch(`http://localhost:5000/api/products/store/${store.store_id}`);
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

    const res    = await fetch(`http://localhost:5000/api/products/store/${storeId}`);
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
                <button class="admin-action-btn btn-delete" 
                    onclick="deleteSellerProduct(${p.id}, '${p.name.replace(/'/g,"\\'")}')">🗑️ Xóa</button>
            </td>
        </tr>
    `).join('');
}

// Mở modal sửa sản phẩm từ Seller Dashboard
async function openEditSellerProduct(productId) {
  try {
    const res    = await fetch(`http://localhost:5000/api/products/${productId}`);
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
    document.getElementById('prodRating').value                  = p.rating || 4.5;
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
    const response = await fetch('http://localhost:5000/api/dang-nhap', {
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

      const maQuyen = currentUser.ma_nhom_quyen || currentUser.Role_id;
      if (maQuyen === 20) {
        switchViewMode('admin');

      }
      else if (maQuyen==13){
        await loadSellerStore();
        switchViewMode('user');
      }
      else {
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
async function loadSellerStore() {
  try {
    const res    = await fetch(`http://localhost:5000/api/stores/by-user/${currentUser.ma_user}`);
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
    const response = await fetch('http://localhost:5000/api/dang-ky', {
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

// Kiểm tra quyền truy cập khu vực Admin dựa trên dữ liệu phân quyền thật từ DB
async function checkAdminAccessButton(ma_nhom_quyen) {
  const btn = document.getElementById('btnGoAdminFromProfile');
  if (!btn) return;

  const ma_user = currentUser.ma_user || currentUser.UserId;

  try {
    const res    = await fetch(`http://localhost:5000/api/quyen-cua-user/${ma_user}`);
    const result = await res.json();

    const hasAnyPermission = result.status === true
      && Array.isArray(result.data)
      && result.data.some(q => q.xem === true);

    btn.style.display = hasAnyPermission ? 'block' : 'none';

  } catch (e) {
    console.error('Lỗi kiểm tra quyền admin:', e);
    btn.style.display = 'none'; // Lỗi → ẩn cho an toàn
  }
}
// Cache quyền của admin đang đăng nhập
let currentAdminPermissions = [];

// Gọi hàm này sau khi login thành công (thay loadAndApplyAdminPermissions)
async function loadAndApplyAdminPermissions(ma_user) {
  try {
    const res    = await fetch(`http://localhost:5000/api/quyen-cua-user/${ma_user}`);
    const result = await res.json();

    if (result.status === true) {
      // Lưu vào cache
      currentAdminPermissions = result.data;

      const tatCaMenu = [
        'menu-dashboard', 'menu-products', 'menu-categories',
        'menu-orders',    'menu-sellers',  'menu-users',
        'menu-vouchers',  'menu-permissions'
      ];

      // Map module_id → menu element
      const menuMap = {
        1: 'menu-products',
        2: 'menu-orders',
        3: 'menu-permissions',
        4: 'menu-categories',
        5: 'menu-dashboard',
        6: 'menu-sellers',
        7: 'menu-users',
        8: 'menu-vouchers'
      };

      // Ẩn tất cả trước
      tatCaMenu.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
      });

      // Chỉ hiện menu có quyền xem
      result.data.forEach(quyen => {
        if (quyen.xem === true && menuMap[quyen.ma_chuc_nang]) {
          const el = document.getElementById(menuMap[quyen.ma_chuc_nang]);
          if (el) el.style.display = 'block';
        }
      });

      // Bấm vào tab đầu tiên có quyền
      const firstVisible = tatCaMenu.find(id => {
        const el = document.getElementById(id);
        return el && el.style.display !== 'none';
      });
      if (firstVisible) {
        const tabName = firstVisible.replace('menu-', '');
        switchAdminTab(tabName);
      }
    }
  } catch (e) {
    console.error("Lỗi tải menu phân quyền:", e);
  }
}

// Kiểm tra quyền theo module
// moduleMap: tab name → module id (khớp với sysModules)
const TAB_MODULE_MAP = {
  'dashboard'  : 5,
  'products'   : 1,
  'categories' : 4,
  'orders'     : 2,
  'sellers'    : 6,
  'users'      : 7,
  'vouchers'   : 8,
  'permissions': 3,
};

function hasPermission(tabName, action = 'xem') {
  const moduleId = TAB_MODULE_MAP[tabName];
  if (!moduleId) return true; // Không map → cho qua

  const quyen = currentAdminPermissions.find(q => q.ma_chuc_nang === moduleId);
  if (!quyen) return false;
  return quyen[action] === true;
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

  // Gọi hàm load dữ liệu tương ứng
  if (tabName === 'dashboard')   initAdminDashboard();
  if (tabName === 'products')    renderAdminProducts();
  if (tabName === 'categories')  renderAdminCategories();
  if (tabName === 'orders') {
    allAdminOrders = []; // Reset để load lại
    renderAdminOrders();
  }
  if (tabName === 'sellers')     renderAdminSellers();
  if (tabName === 'users') {
  renderUserRoleFilter();
  renderAdminUsers();
}
  if (tabName === 'vouchers')    renderAdminVouchers?.();
  if (tabName === 'permissions') {
    renderPermissionsTable();
    renderGroupPermTable();
    switchPermTab('user');
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
  currentAdminPermissions = [];
   xoaDangNhap();

  // Reset topbar & nút header
  document.getElementById('topbarUserText').textContent  = '👤 Chưa đăng nhập';
  document.getElementById('authBtnLabel').textContent    = 'Đăng nhập';
  document.getElementById('hdrAuthBtn').style.display = 'flex';
document.getElementById('hdrUserBtn').style.display = 'none';
  document.getElementById('hdrAuthBtn').style.display    = 'flex';
  document.getElementById('hdrRegisterSellerBtn').style.display = 'none';
  document.getElementById('hdrGoSellerBtn').style.display = 'none';

  // Ẩn các nút chỉ hiện khi đã đăng nhập
  ['hdrProfileBtn', 'hdrHistoryBtn',  'hdrSellerBtn'].forEach(id => {
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






// Cập nhật sysModules để id khớp với menuMap trên
const sysModules = [
  { id: 1, name: 'Quản lý Sản phẩm'   },
  { id: 2, name: 'Quản lý Đơn hàng'   },
  { id: 3, name: 'Quản lý Phân quyền' },
  { id: 4, name: 'Quản lý Danh mục'   },
  { id: 5, name: 'Thống kê Doanh thu'  },  // ← Thêm
  { id: 6, name: 'Quản lý Người bán'  },
  { id: 7, name: 'Quản lý Tài khoản'  },  // ← Thêm
];
// Load users vào dropdown trong panel nhóm
async function loadUsersForGroupApply() {
  const select = document.getElementById('applyGroupToUserSelect');
  if (!select) return;
  try {
    const res    = await fetch('http://localhost:5000/api/users');
    const result = await res.json();
    if (result.status && Array.isArray(result.data)) {
      select.innerHTML = '<option value="">-- Chọn tài khoản --</option>';
      result.data.forEach(u => {
        const opt = document.createElement('option');
        opt.value       = u.ma_user;
        opt.textContent = `#${u.ma_user} ${u.ten_user} [${u.ten_nhom_quyen || '?'}]`;
        select.appendChild(opt);
      });
    }
  } catch (e) { console.error('Lỗi load users:', e); }
}

// Áp dụng quyền của nhóm đang chọn xuống 1 user cụ thể
async function apDungQuyenNhomChoUserTuPanel() {
  const groupId = document.getElementById('permGroupSelect').value;
  const userId  = document.getElementById('applyGroupToUserSelect').value;

  if (!groupId) { showToast('⚠️ Vui lòng chọn nhóm quyền!'); return; }
  if (!userId)  { showToast('⚠️ Vui lòng chọn tài khoản!');  return; }

  if (!confirm('Áp dụng quyền của nhóm này cho tài khoản đã chọn?\nQuyền ngoại lệ hiện tại sẽ bị ghi đè.')) return;

  // Lấy quyền hiện tại của nhóm từ checkbox bảng
  const permissions = sysModules.map(m => ({
    ma_chuc_nang: m.id,
    xem  : document.querySelector(`.grp-view[data-mod="${m.id}"]`)?.checked   || false,
    them : document.querySelector(`.grp-add[data-mod="${m.id}"]`)?.checked    || false,
    sua  : document.querySelector(`.grp-edit[data-mod="${m.id}"]`)?.checked   || false,
    xoa  : document.querySelector(`.grp-delete[data-mod="${m.id}"]`)?.checked || false,
  }));

  try {
    const res    = await fetch('http://localhost:5000/api/cap-quyen-ngoai-le', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ ma_user: userId, permissions })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + result.message);
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
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

async function initAdminDashboard() {
  try {
    const res    = await fetch('http://localhost:5000/api/thong-ke/tong-quan');
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
  const res    = await fetch('http://localhost:5000/api/thong-ke/doanh-thu-theo-thang?year=2026');
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
  if (sort === 'rating')     filtered.sort((a, b) => (b.rating||0) - (a.rating||0));
  if (sort === 'bestseller') filtered.sort((a, b) => (b.sold||0) - (a.sold||0));

  renderUserProducts(filtered);
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
    Description: document.getElementById('sellerDesc').value.trim()
    // ✅ Không cần gửi NationalId — backend tự lấy từ hồ sơ user
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

  currentFilteredProducts = arr || [];

  if (!arr || arr.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <div class="icon">📦</div>
        <p>Không có sản phẩm nào</p>
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
          <span style="font-size:11px; color:var(--text-muted);">⭐ ${p.rating || 4.5} · Đã bán ${p.sold || 0}</span>
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
  const canDelete = hasPermission('products', 'xoa');
  const showActionCol = canEdit || canDelete; // Có ít nhất 1 quyền mới hiện cột

  // Ẩn/hiện nút Thêm
  const btnAdd = document.querySelector('#pane-products .checkout-btn');
  if (btnAdd) btnAdd.style.display = canAdd ? '' : 'none';

  try {
    const res    = await fetch('http://localhost:5000/api/products');
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
          ${canDelete
            ? `<button class="admin-action-btn btn-delete"
                        onclick="deleteSellerProduct(${p.id}, '${p.name.replace(/'/g, "\\'")}')">🗑️ Xóa</button>`
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
  document.getElementById('prodRating').value    = '4.5';
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
    const res    = await fetch(`http://localhost:5000/api/products/${productId}`);
    const result = await res.json();

    if (!result.status) { showToast('❌ Không tìm thấy sản phẩm!'); return; }

    const p = result.data;

    document.getElementById('adminProductModalTitle').textContent = '✏️ Chỉnh sửa sản phẩm';
    document.getElementById('editProductId').value = p.id;
    document.getElementById('prodName').value      = p.name;
    document.getElementById('prodPrice').value     = p.price;
    document.getElementById('prodOldPrice').value  = p.old_price || '';
    document.getElementById('prodStock').value     = p.quantity;
    document.getElementById('prodRating').value    = p.rating || 4.5;
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
    const res    = await fetch('http://localhost:5000/api/categories');
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
            const checkRes    = await fetch(`http://localhost:5000/api/products/${productId}`);
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
        rating      : document.getElementById('prodRating').value || 4.5,
        emoji       : emoji,
        description : document.getElementById('prodDesc').value.trim(),
        category_id : categoryId,
        store_id    : storeId
    };

    // ── 5. Gọi API ───────────────────────────────────────────
    const url    = isEdit
        ? `http://localhost:5000/api/products/${productId}`
        : `http://localhost:5000/api/products`;
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

// ─── XÓA SẢN PHẨM ────────────────────────────────────────────────────────────
async function deleteSellerProduct(productId, productName) {
    if (!confirm(`Xóa sản phẩm "${productName}"?`)) return;
    try {
        const res    = await fetch(`http://localhost:5000/api/products/${productId}`, {
            method: 'DELETE'
        });
        const result = await res.json();
        showToast(result.status ? '✅ ' + result.message : '❌ ' + result.message);

        if (result.status) {
            // Reload bảng sản phẩm (seller hoặc admin)
            const isSellerMode = !!currentUser?.store;
            if (isSellerMode) {
                renderSellerProducts();
            } else {
                renderAdminProducts();  // ← đang ở admin thì reload bảng admin
            }

            loadProducts();        // ← cập nhật trang user
            initAdminDashboard();  // ← cập nhật lại thống kê tổng sản phẩm
        }
    } catch (e) {
        showToast('❌ Lỗi kết nối!');
    }
}

// ─── RENDER DANH MỤC ADMIN ───────────────────────────────────────────────────
async function renderAdminCategories() {
  const tbody = document.getElementById('tblCategoriesBody');
  tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:20px; color:var(--text-muted);">Đang tải...</td></tr>`;

  try {
    const res    = await fetch('http://localhost:5000/api/categories');
    const result = await res.json();

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">Chưa có danh mục nào</td></tr>`;
      return;
    }

    tbody.innerHTML = result.data.map(c => `
      <tr>
        <td style="font-size:20px; text-align:center;">📁</td>
        <td style="font-weight:600;">${c.name}</td>
        <td><code style="background:var(--bg); padding:2px 6px; border-radius:4px; font-size:12px;">${c.id}</code></td>
        <td style="text-align:center;">—</td>
        <td>
          <button class="admin-action-btn btn-edit" onclick="editCategory(${c.id}, '${c.name.replace(/'/g, "\\'")}')">✏️ Sửa</button>
          <button class="admin-action-btn btn-delete" onclick="deleteCategory(${c.id}, '${c.name.replace(/'/g, "\\'")}')">🗑️ Xóa</button>
        </td>
      </tr>
    `).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
  }
}

// ─── THÊM DANH MỤC ───────────────────────────────────────────────────────────
async function addCategory() {
  const name = document.getElementById('newCatName').value.trim();
  if (!name) { showToast('⚠️ Tên danh mục không được trống!'); return; }

  try {
    const res    = await fetch('http://localhost:5000/api/categories', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ name })
    });
    const result = await res.json();

    if (result.status) {
      showToast('✅ ' + result.message);
      document.getElementById('newCatName').value  = '';
      document.getElementById('newCatEmoji').value = '';
      document.getElementById('newCatSlug').value  = '';
      renderAdminCategories();
      loadCategories(); // Cập nhật dropdown khắp nơi
    } else {
      showToast('❌ ' + result.message);
    }

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ─── SỬA DANH MỤC ────────────────────────────────────────────────────────────
async function editCategory(categoryId, currentName) {
  const newName = prompt(`Nhập tên mới cho danh mục:`, currentName);
  if (!newName || newName.trim() === currentName) return;

  try {
    const res    = await fetch(`http://localhost:5000/api/categories/${categoryId}`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ name: newName.trim() })
    });
    const result = await res.json();

    if (result.status) {
      showToast('✅ ' + result.message);
      renderAdminCategories();
      loadCategories();
    } else {
      showToast('❌ ' + result.message);
    }

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}

// ─── XÓA DANH MỤC ────────────────────────────────────────────────────────────
async function deleteCategory(categoryId, categoryName) {
  if (!confirm(`Xóa danh mục "${categoryName}"?\nCác sản phẩm thuộc danh mục này có thể bị ảnh hưởng!`)) return;

  try {
    const res    = await fetch(`http://localhost:5000/api/categories/${categoryId}`, {
      method: 'DELETE'
    });
    const result = await res.json();

    if (result.status) {
      showToast('✅ ' + result.message);
      renderAdminCategories();
      loadCategories();
    } else {
      showToast('❌ ' + result.message);
    }

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
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
    document.getElementById('prodRating').value    = '4.5';
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

  if (!allRoles.length) await loadAllRoles();

  try {
    const res    = await fetch('http://localhost:5000/api/users');
    const result = await res.json();

    if (!result.status || !result.data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                         color:var(--text-muted);">Không có tài khoản nào</td></tr>`;
      return;
    }

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
      const targetRole = allRoles.find(r =>
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

      // ✅ Đọc trang_thai từ backend
      const isBanned   = u.trang_thai === 'banned';
      const statusHtml = isBanned
        ? `<span style="background:#fee2e2; color:#dc2626; padding:3px 10px;
                        border-radius:99px; font-size:11px; font-weight:700;">🔒 Đã khóa</span>`
        : `<span style="background:#dcfce7; color:#16a34a; padding:3px 10px;
                        border-radius:99px; font-size:11px; font-weight:700;">✅ Hoạt động</span>`;

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
          <td>
            ${isMe
              ? `<span style="font-size:12px; color:var(--text-muted);">Tài khoản của bạn</span>`
              : `<button class="admin-action-btn btn-edit"
                   onclick="openEditUserModal(
                     ${u.ma_user},
                     '${u.ten_user.replace(/'/g,"\\'")}',
                     ${u.ma_nhom_quyen},
                     '${isBanned ? 'banned' : 'active'}')">
                   ✏️ Sửa
                 </button>`
            }
          </td>
        </tr>
      `;
    }).join('');

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;
                       color:var(--red);">❌ Lỗi tải dữ liệu</td></tr>`;
  }
}

// ─── MỞ MODAL CHỈNH SỬA USER ─────────────────────────────────────────────────
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

  if (!allRoles.length) await loadAllRoles();

  // Dropdown vai trò — động
  document.getElementById('editUserRole').innerHTML = allRoles.map(r => `
    <option value="${r.RoleId}" ${r.RoleId === ma_nhom_quyen ? 'selected' : ''}>
      ${r.RoleName}
    </option>
  `).join('');

  // ✅ Set đúng trạng thái hiện tại
  document.getElementById('editUserStatus').value = currentStatus;

  document.getElementById('adminUserModal').classList.add('show');
}

// ─── LƯU THAY ĐỔI VAI TRÒ ────────────────────────────────────────────────────
async function handleSaveUserRole() {
  const ma_user   = document.getElementById('editUserId').value;
  const role_id   = document.getElementById('editUserRole').value;
  const newStatus = document.getElementById('editUserStatus').value;

  if (!ma_user) { showToast('⚠️ Thiếu thông tin!'); return; }

  try {
    // Gọi song song 2 API: cập nhật role + cập nhật status
    const [resRole, resStatus] = await Promise.all([
      fetch(`http://localhost:5000/api/users/${ma_user}/role`, {
        method : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ role_id: parseInt(role_id) })
      }),
      fetch(`http://localhost:5000/api/users/${ma_user}/status`, {
        method : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ status: newStatus })
      })
    ]);

    const [rRole, rStatus] = await Promise.all([resRole.json(), resStatus.json()]);

    if (rRole.status && rStatus.status) {
      showToast('✅ Đã cập nhật vai trò và trạng thái!');
      closeModal('adminUserModal');
      renderAdminUsers();
    } else {
      const errMsg = (!rRole.status ? rRole.message : '') ||
                     (!rStatus.status ? rStatus.message : '');
      showToast('❌ ' + errMsg);
    }

  } catch (e) {
    showToast('❌ Lỗi kết nối!');
  }
}
// ==========================================
// PHÂN QUYỀN — REFACTOR HOÀN TOÀN
// ==========================================

let currentPermTab = 'user';

function switchPermTab(tab) {
  currentPermTab = tab;
  const isUser = tab === 'user';

  const btnUser  = document.getElementById('btnPermTabUser');
  const btnGroup = document.getElementById('btnPermTabGroup');
  if (btnUser) {
    btnUser.style.background = isUser ? 'var(--primary)' : 'white';
    btnUser.style.color      = isUser ? 'white' : 'var(--text)';
    btnUser.style.border     = isUser ? 'none' : '1px solid var(--border)';
  }
  if (btnGroup) {
    btnGroup.style.background = isUser ? 'white' : 'var(--primary)';
    btnGroup.style.color      = isUser ? 'var(--text)' : 'white';
    btnGroup.style.border     = isUser ? '1px solid var(--border)' : 'none';
  }

  const panelUser  = document.getElementById('permPanelUser');
  const panelGroup = document.getElementById('permPanelGroup');
  if (panelUser)  panelUser.style.display  = isUser ? 'block' : 'none';
  if (panelGroup) panelGroup.style.display = isUser ? 'none'  : 'block';

  if (isUser) {
    loadUsersToDropdown();
    renderPermissionsTable();
  } else {
    loadRolesForPermPanel();
    renderGroupPermTable();
    loadUsersForGroupApply();
  }
}

// ── PANEL CÁ NHÂN ─────────────────────────────────────────────
async function loadUsersToDropdown() {
  const selectBox = document.getElementById('permUserSelect');
  if (!selectBox) return;
  try {
    const res    = await fetch('http://localhost:5000/api/users');
    const result = await res.json();
    if (result.status && Array.isArray(result.data)) {
      selectBox.innerHTML = '<option value="">-- Chọn tài khoản --</option>';
      result.data.forEach(u => {
        const id   = u.ma_user || u.UserId;
        const name = u.ten_user || u.FullName || '?';
        const role = u.ten_nhom_quyen || u.RoleName || '';
        const opt  = document.createElement('option');
        opt.value       = id;
        opt.textContent = `#${id} ${name} [${role}]`;
        selectBox.appendChild(opt);
      });
    }
  } catch (e) {
    showToast('❌ Không thể tải danh sách tài khoản!');
  }
}

function renderPermissionsTable() {
  const tbody = document.getElementById('tblPermissionsBody');
  if (!tbody) return;
  tbody.innerHTML = sysModules.map(m => `
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:10px; border-right:1px solid var(--border); font-weight:500;">${m.name}</td>
      <td style="text-align:center;"><input type="checkbox" class="cb-view"   data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="cb-add"    data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="cb-edit"   data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="cb-delete" data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
    </tr>
  `).join('');
}

async function loadPermissionsData() {
  const userId = document.getElementById('permUserSelect').value;
  if (!userId) { showToast('⚠️ Vui lòng chọn tài khoản!'); return; }
  try {
    const res    = await fetch(`http://localhost:5000/api/quyen-cua-user/${userId}`);
    const result = await res.json();
    if (result.status) {
      document.querySelectorAll('#tblPermissionsBody input[type="checkbox"]')
        .forEach(cb => cb.checked = false);
      result.data.forEach(q => {
        if (q.xem)  { const el = document.querySelector(`.cb-view[data-mod="${q.ma_chuc_nang}"]`);   if (el) el.checked = true; }
        if (q.them) { const el = document.querySelector(`.cb-add[data-mod="${q.ma_chuc_nang}"]`);    if (el) el.checked = true; }
        if (q.sua)  { const el = document.querySelector(`.cb-edit[data-mod="${q.ma_chuc_nang}"]`);   if (el) el.checked = true; }
        if (q.xoa)  { const el = document.querySelector(`.cb-delete[data-mod="${q.ma_chuc_nang}"]`); if (el) el.checked = true; }
      });
      showToast('✅ Đã tải quyền của tài khoản!');
    }
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

function capTatCaQuyenUser() {
  document.querySelectorAll('#tblPermissionsBody input[type="checkbox"]')
    .forEach(cb => cb.checked = true);
  showToast('✅ Đã chọn tất cả quyền!');
}

function thuHoiTatCaQuyenUser() {
  document.querySelectorAll('#tblPermissionsBody input[type="checkbox"]')
    .forEach(cb => cb.checked = false);
  showToast('❌ Đã bỏ tất cả quyền!');
}

async function savePermissionsData() {
  const userId = document.getElementById('permUserSelect').value;
  if (!userId) { showToast('⚠️ Vui lòng chọn tài khoản!'); return; }
  const permissions = sysModules.map(m => ({
    ma_chuc_nang: m.id,
    xem  : document.querySelector(`.cb-view[data-mod="${m.id}"]`)?.checked   || false,
    them : document.querySelector(`.cb-add[data-mod="${m.id}"]`)?.checked    || false,
    sua  : document.querySelector(`.cb-edit[data-mod="${m.id}"]`)?.checked   || false,
    xoa  : document.querySelector(`.cb-delete[data-mod="${m.id}"]`)?.checked || false,
  }));
  try {
    const res    = await fetch('http://localhost:5000/api/cap-quyen-ngoai-le', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ ma_user: userId, permissions })
    });
    const result = await res.json();
    showToast((result.status ? '💾 ' : '❌ ') + result.message);
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

async function apDungQuyenNhomChoUser() {
  const userId = document.getElementById('permUserSelect').value;
  if (!userId) { showToast('⚠️ Vui lòng chọn tài khoản!'); return; }
  if (!confirm('Thao tác này sẽ XÓA mọi quyền ngoại lệ và đặt lại về quyền mặc định của nhóm. Tiếp tục?')) return;
  try {
    const res    = await fetch('http://localhost:5000/api/ap-dung-quyen-nhom-cho-user', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ ma_user: userId })
    });
    const result = await res.json();
    showToast((result.status ? '✅ ' : '❌ ') + result.message);
    if (result.status) loadPermissionsData();
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

// ── PANEL NHÓM QUYỀN ──────────────────────────────────────────
async function loadRolesForPermPanel() {
  try {
    const res    = await fetch('http://localhost:5000/api/roles');
    const result = await res.json();
    if (!result.status) return;
    const roles = result.data;

    const select = document.getElementById('permGroupSelect');
    if (select) {
      select.innerHTML = '<option value="">-- Chọn nhóm --</option>' +
        roles.map(r => `<option value="${r.RoleId}">${r.RoleId}. ${r.RoleName}</option>`).join('');
    }
     const content = document.getElementById('rolesManagerContent');
    if (content && content.style.display !== 'none') {
      renderRolesList(roles);
    }
  } catch (e) { showToast('❌ Lỗi tải danh sách nhóm!'); }
}

function renderRolesList(roles) {
  const tbody = document.getElementById('tblRolesList');
  if (!tbody) return;
  if (!roles.length) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:10px;
                       color:var(--text-muted);">Chưa có nhóm nào</td></tr>`;
    return;
  }
  tbody.innerHTML = roles.map(r => `
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:7px 10px; color:var(--text-muted); font-size:12px;">#${r.RoleId}</td>
      <td style="padding:7px 10px;">
        <span id="roleName_${r.RoleId}">${r.RoleName}</span>
        <input type="text" id="roleNameInput_${r.RoleId}" value="${r.RoleName}"
          style="display:none; padding:4px 8px; border:1px solid var(--border);
                 border-radius:4px; font-family:inherit; font-size:13px; width:80%;">
      </td>
      <td style="padding:7px 10px; text-align:center;">
        <button class="admin-action-btn btn-edit"   id="btnEdit_${r.RoleId}"
          onclick="batDauSuaRole(${r.RoleId})">✏️ Sửa</button>
        <button class="admin-action-btn btn-confirm" id="btnSave_${r.RoleId}"
          onclick="luuSuaRole(${r.RoleId})" style="display:none;">💾 Lưu</button>
        <button class="admin-action-btn btn-cancel"  id="btnCancel_${r.RoleId}"
          onclick="huyySuaRole(${r.RoleId})" style="display:none;">✕</button>
        <button class="admin-action-btn btn-delete"
          onclick="xoaNhomQuyen(${r.RoleId}, '${r.RoleName.replace(/'/g,"\\'")}')">🗑️ Xóa</button>
      </td>
    </tr>
  `).join('');
}

function renderGroupPermTable() {
  const tbody = document.getElementById('tblGroupPermissionsBody');
  if (!tbody) return;
  tbody.innerHTML = sysModules.map(m => `
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:10px; border-right:1px solid var(--border); font-weight:500;">${m.name}</td>
      <td style="text-align:center;"><input type="checkbox" class="grp-view"   data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="grp-add"    data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="grp-edit"   data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
      <td style="text-align:center;"><input type="checkbox" class="grp-delete" data-mod="${m.id}" style="transform:scale(1.3); cursor:pointer;"></td>
    </tr>
  `).join('');
}

function onGroupSelectChange() {
  document.querySelectorAll('#tblGroupPermissionsBody input[type="checkbox"]')
    .forEach(cb => cb.checked = false);
}

async function loadGroupPermissions() {
  const groupId = document.getElementById('permGroupSelect').value;
  if (!groupId) { showToast('⚠️ Vui lòng chọn nhóm quyền!'); return; }
  try {
    const res    = await fetch(`http://localhost:5000/api/quyen-cua-nhom/${groupId}`);
    const result = await res.json();
    if (result.status) {
      document.querySelectorAll('#tblGroupPermissionsBody input[type="checkbox"]')
        .forEach(cb => cb.checked = false);
      result.data.forEach(q => {
        if (q.xem)  { const el = document.querySelector(`.grp-view[data-mod="${q.ma_chuc_nang}"]`);   if (el) el.checked = true; }
        if (q.them) { const el = document.querySelector(`.grp-add[data-mod="${q.ma_chuc_nang}"]`);    if (el) el.checked = true; }
        if (q.sua)  { const el = document.querySelector(`.grp-edit[data-mod="${q.ma_chuc_nang}"]`);   if (el) el.checked = true; }
        if (q.xoa)  { const el = document.querySelector(`.grp-delete[data-mod="${q.ma_chuc_nang}"]`); if (el) el.checked = true; }
      });
      showToast('✅ Đã tải quyền của nhóm!');
    }
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

function capTatCaQuyenGroup() {
  document.querySelectorAll('#tblGroupPermissionsBody input[type="checkbox"]')
    .forEach(cb => cb.checked = true);
  showToast('✅ Đã chọn tất cả quyền nhóm!');
}

function thuHoiTatCaQuyenGroup() {
  document.querySelectorAll('#tblGroupPermissionsBody input[type="checkbox"]')
    .forEach(cb => cb.checked = false);
  showToast('❌ Đã bỏ tất cả quyền nhóm!');
}

async function saveGroupPermissions() {
  const groupId = document.getElementById('permGroupSelect').value;
  if (!groupId) { showToast('⚠️ Vui lòng chọn nhóm!'); return; }
  const permissions = sysModules.map(m => ({
    ma_chuc_nang: m.id,
    xem  : document.querySelector(`.grp-view[data-mod="${m.id}"]`)?.checked   || false,
    them : document.querySelector(`.grp-add[data-mod="${m.id}"]`)?.checked    || false,
    sua  : document.querySelector(`.grp-edit[data-mod="${m.id}"]`)?.checked   || false,
    xoa  : document.querySelector(`.grp-delete[data-mod="${m.id}"]`)?.checked || false,
  }));
  try {
    const res    = await fetch('http://localhost:5000/api/cap-quyen-nhom', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ role_id: groupId, permissions })
    });
    const result = await res.json();
    showToast((result.status ? '💾 ' : '❌ ') + result.message);
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

// ── CRUD NHÓM QUYỀN ───────────────────────────────────────────
async function themNhomQuyen() {
  const name = document.getElementById('newRoleName').value.trim();
  if (!name) { showToast('⚠️ Nhập tên nhóm quyền!'); return; }
  try {
    const res    = await fetch('http://localhost:5000/api/roles', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ role_name: name })
    });
    const result = await res.json();
    if (result.status) {
      showToast('✅ ' + result.message);
      document.getElementById('newRoleName').value = '';
      loadRolesForPermPanel(); // reload cả dropdown lẫn bảng
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

function batDauSuaRole(roleId) {
  document.getElementById(`roleName_${roleId}`).style.display      = 'none';
  document.getElementById(`roleNameInput_${roleId}`).style.display = 'inline-block';
  document.getElementById(`btnEdit_${roleId}`).style.display       = 'none';
  document.getElementById(`btnSave_${roleId}`).style.display       = 'inline-block';
  document.getElementById(`btnCancel_${roleId}`).style.display     = 'inline-block';
}

function huyySuaRole(roleId) {
  document.getElementById(`roleName_${roleId}`).style.display      = 'inline';
  document.getElementById(`roleNameInput_${roleId}`).style.display = 'none';
  document.getElementById(`btnEdit_${roleId}`).style.display       = 'inline-block';
  document.getElementById(`btnSave_${roleId}`).style.display       = 'none';
  document.getElementById(`btnCancel_${roleId}`).style.display     = 'none';
}

async function luuSuaRole(roleId) {
  const newName = document.getElementById(`roleNameInput_${roleId}`).value.trim();
  if (!newName) { showToast('⚠️ Tên nhóm không được trống!'); return; }
  try {
    const res    = await fetch(`http://localhost:5000/api/roles/${roleId}`, {
      method : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ role_name: newName })
    });
    const result = await res.json();
    if (result.status) {
      showToast('✅ ' + result.message);
      loadRolesForPermPanel();
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}

async function xoaNhomQuyen(roleId, roleName) {
  if (!confirm(`Xóa nhóm quyền "${roleName}"?\nTất cả quyền của nhóm này sẽ bị xóa theo!`)) return;
  try {
    const res    = await fetch(`http://localhost:5000/api/roles/${roleId}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status) {
      showToast('✅ ' + result.message);
      loadRolesForPermPanel();
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) { showToast('❌ Lỗi kết nối!'); }
}
async function loadCartFromServer() {
  if (!currentUser) return;
  try {
    const userId = currentUser.ma_user || currentUser.UserId;
    const res    = await fetch(`http://localhost:5000/api/gio-hang/${userId}`);
    const result = await res.json();

    if (result.status === true && Array.isArray(result.data)) {
      // Map về đúng cấu trúc mà handlePlaceOrder cần
      cart = result.data.map(item => ({
        ProductId  : item.ProductId   || item.product_id,
        ProductName: item.ProductName || item.product_name || item.name || `Sản phẩm #${item.ProductId || item.product_id}`,
        Emoji      : item.Emoji       || item.emoji        || '📦',
        ImageUrl  : item.ImageUrl || item.image_url || '',
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
        const res = await fetch('http://localhost:5000/api/gio-hang/them', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                UserId   : currentUser.ma_user || currentUser.UserId,
                ProductId: productId,
                Quantity : quantity,
                UnitPrice: unitPrice,
                Force    : force
            })
        });
        const result = await res.json();

        if (result.status === true) {
            showToast("🛒 " + result.message);
            loadCartFromServer();
            return;
        }

        // ✅ Giỏ đang có shop khác — hỏi xác nhận đổi
        if (result.conflict) {
            const xacNhan = confirm(`⚠️ ${result.message}`);
            if (xacNhan) {
                await xuLyThemVaoGio(productId, quantity, unitPrice, true);
            }
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
  const totalAmount = Math.max(0, subtotal + currentShippingFee - currentVoucherDiscount);

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
    Discount       : currentVoucherDiscount,
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
    const response = await fetch('http://localhost:5000/api/don-hang/dat-hang', {
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
      currentVoucherDiscount = 0;
      currentShippingFee = 25000;
      updateCartBadge();
      renderCartItems();
    } else {
      showToast('❌ ' + result.message);
    }
  } catch (e) {
    showToast('❌ Lỗi hệ thống khi đặt hàng!');
    console.error(e);
  }
}
// ─── RENDER GIAO DIỆN GIỎ HÀNG ─────────────────────────────────────────────
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
    const res    = await fetch('http://localhost:5000/api/gio-hang/xoa', {
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
    const res    = await fetch('http://localhost:5000/api/gio-hang/cap-nhat', {
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

function recalcOrderTotal() {
  const buyerCity = document.getElementById('chkBuyerCity').value;
  currentShippingFee = getShippingFee(buyerCity);

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
  const total = subtotal + currentShippingFee - currentVoucherDiscount;

  document.getElementById('checkoutSubtotalText').textContent =
    subtotal.toLocaleString('vi-VN') + 'đ';
  document.getElementById('checkoutShipText').textContent =
    currentShippingFee.toLocaleString('vi-VN') + 'đ';
  document.getElementById('checkoutTotalText').textContent =
    Math.max(0, total).toLocaleString('vi-VN') + 'đ';
}

function togglePaymentDetails(val) {
  document.getElementById('bankDetailsBlock').style.display = val === 'BANK'    ? 'block' : 'none';
  document.getElementById('momoBlock').style.display        = val === 'MOMO'    ? 'block' : 'none';
  document.getElementById('zalopayBlock').style.display     = val === 'ZALOPAY' ? 'block' : 'none';
}

function applyCheckoutVoucher() {
  const code = document.getElementById('checkoutVoucherInput').value.trim().toUpperCase();
  const msgEl = document.getElementById('checkoutVoucherMsg');
  const discRow = document.getElementById('checkoutDiscRow');
  const discText = document.getElementById('checkoutDiscText');

  // Danh sách voucher mẫu — sau này thay bằng gọi API
  const vouchers = {
    'POBBY10': { type: 'percent', value: 10, minOrder: 0 },
    'SHIP0':   { type: 'fixed',   value: 25000, minOrder: 100000 },
    'SALE50K': { type: 'fixed',   value: 50000, minOrder: 200000 },
  };

  const subtotal = cart.reduce((sum, item) => sum + (item.Quantity * item.UnitPrice), 0);
  const v = vouchers[code];

  if (!v) {
    msgEl.style.color = 'red';
    msgEl.textContent = '❌ Mã voucher không hợp lệ!';
    currentVoucherDiscount = 0;
    discRow.style.display = 'none';
    updateCheckoutSummary();
    return;
  }
  if (subtotal < v.minOrder) {
    msgEl.style.color = 'red';
    msgEl.textContent = `❌ Đơn hàng tối thiểu ${v.minOrder.toLocaleString('vi-VN')}đ để dùng mã này!`;
    currentVoucherDiscount = 0;
    discRow.style.display = 'none';
    updateCheckoutSummary();
    return;
  }

  currentVoucherDiscount = v.type === 'percent'
    ? Math.floor(subtotal * v.value / 100)
    : v.value;

  msgEl.style.color = 'green';
  msgEl.textContent = `✅ Áp dụng mã thành công! Giảm ${currentVoucherDiscount.toLocaleString('vi-VN')}đ`;
  discRow.style.display = 'flex';
  discText.textContent = '-' + currentVoucherDiscount.toLocaleString('vi-VN') + 'đ';

  updateCheckoutSummary();
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

  // Reset voucher mỗi lần mở
  currentVoucherDiscount = 0;
  document.getElementById('checkoutVoucherInput').value = '';
  document.getElementById('checkoutVoucherMsg').textContent = '';
  document.getElementById('checkoutDiscRow').style.display = 'none';

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
      const res    = await fetch('http://localhost:5000/api/don-hang/tat-ca');
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
    const res    = await fetch(`http://localhost:5000/api/don-hang/${orderId}/trang-thai`, {
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
    const res    = await fetch(`http://localhost:5000/api/don-hang/cua-toi/${userId}`);
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
          <div style="padding:8px 14px; border-top:1px solid var(--border); text-align:right;">
            <button onclick="huyDonHangCuaToi(${o.OrderId})"
              style="background:none; border:1px solid var(--red); color:var(--red);
                     border-radius:6px; padding:5px 14px; cursor:pointer;
                     font-family:inherit; font-size:13px;">
              ❌ Hủy đơn hàng
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

// Hủy đơn từ phía khách hàng (chỉ khi Pending)
async function huyDonHangCuaToi(orderId) {
  if (!confirm(`Xác nhận hủy đơn hàng #${orderId}?`)) return;
  try {
    const res    = await fetch(`http://localhost:5000/api/don-hang/${orderId}/trang-thai`, {
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
    const res    = await fetch(`http://localhost:5000/api/don-hang/cua-toi/${userId}`);
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
function toggleRolesManager() {
  const content = document.getElementById('rolesManagerContent');
  const btn     = document.getElementById('btnToggleRolesManager');
  const isHidden = content.style.display === 'none';

  content.style.display = isHidden ? 'block' : 'none';
  btn.textContent       = isHidden ? '➖ Thu gọn' : '➕ Mở rộng';

  // Lần đầu mở → load danh sách roles
  if (isHidden) loadRolesForPermPanel();
}
// Cache roles động từ API
let allRoles = [];

async function loadAllRoles() {
  try {
    const res    = await fetch('http://localhost:5000/api/roles');
    const result = await res.json();
    if (result.status && Array.isArray(result.data)) {
      allRoles = result.data; // [{ RoleId, RoleName }, ...]
    }
  } catch (e) {
    console.error('Lỗi load roles:', e);
  }
}

// Lấy tên role theo ID — dùng trong renderAdminUsers
function getRoleName(roleId) {
  const r = allRoles.find(r => r.RoleId === roleId);
  return r ? r.RoleName : `Role #${roleId}`;
}

// Lấy class badge theo ID — có thể mở rộng sau
function getRoleCls(roleId) {
  if (roleId === 20) return 'role-admin';
  if (roleId === 13) return 'role-seller';
  if (roleId === 14) return 'role-customer';
  return 'role-customer'; // mặc định
}

// ─── RENDER BẢNG QUẢN LÝ TÀI KHOẢN (ĐỘNG) ───────────────────

// ─── MỞ MODAL CHỈNH SỬA USER — DROPDOWN ĐỘNG ─────────────────
async function openEditUserModal(ma_user, ten_user, ma_nhom_quyen) {
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

  // Đảm bảo roles đã load
  if (!allRoles.length) await loadAllRoles();

  // Đổ tất cả roles vào dropdown động
  const roleSelect = document.getElementById('editUserRole');
  roleSelect.innerHTML = allRoles.map(r => `
    <option value="${r.RoleId}" ${r.RoleId === ma_nhom_quyen ? 'selected' : ''}>
      ${r.RoleName}
    </option>
  `).join('');

  document.getElementById('adminUserModal').classList.add('show');
}
async function renderUserRoleFilter() {
  if (!allRoles.length) await loadAllRoles();
  const select = document.getElementById('userRoleFilter');
  if (!select) return;
  select.innerHTML = `<option value="all">Tất cả vai trò</option>` +
    allRoles.map(r => `<option value="${r.RoleName}">${r.RoleName}</option>`).join('');
}
async function openProductDetail(productId) {
  const content = document.getElementById('productDetailContent');
  content.innerHTML = `<div style="text-align:center; padding:60px 0; color:var(--text-muted);">⏳ Đang tải...</div>`;
  document.getElementById('productDetailModal').classList.add('show');

  try {
    const res    = await fetch(`http://localhost:5000/api/products/${productId}`);
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
            <span>⭐ ${p.rating || 4.5}</span>
            <span>·</span>
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