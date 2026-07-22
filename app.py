import io
import os
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import streamlit as st

# --- 1. SECURITY & MEMORY SAFEGUARDS ---
# Protect against Decompression Bomb DoS attacks
MAX_PIXEL_COUNT = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXEL_COUNT

MAX_IMAGE_WIDTH = 1200
MAX_UPLOAD_SIZE_MB = 3
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

st.set_page_config(page_title="ArtPrintBuddies Visualizer", layout="wide")

# Custom CSS
st.markdown(
    """
    <style>
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
        }
    }
    
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 8px;
        padding: 8px;
        transition: transform 0.2s;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        transform: scale(1.02);
        border: 2px solid #0066cc;
    }
    
    div[data-element-to-test="stMarkdownContainer"] {
        font-weight: 500;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE NAVIGATION INITIALIZATION ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "sanitized_wall_img" not in st.session_state:
    st.session_state.sanitized_wall_img = None
if "selected_art_path" not in st.session_state:
    st.session_state.selected_art_path = None
if "selected_art_name" not in st.session_state:
    st.session_state.selected_art_name = None

# --- BRANDING & SIDEBAR COMPANY DETAILS ---
with st.sidebar:
    st.markdown("# 🖼️ ArtPrintBuddies")
    st.markdown("### 圖畫裝飾")
    st.caption("Powered by Tung Fong Printing Service 東方晒圖")
    st.markdown("---")
    st.write("室內效果預覽工具：上傳您的房間照片，即可模擬裝飾畫掛牆效果。")
    st.write("Upload a photo of your room to see how our decor looks on your wall!")
    st.markdown("---")

    if st.session_state.step == 2:
        if st.button("⬅️ 重選牆面或畫作 / Back to Step 1", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

st.title("🎨 ArtPrintBuddies Wall Art Visualizer")

# ==============================================================================
# 2. HELPER UTILITIES & SECURITY FUNCTIONS
# ==============================================================================
@st.cache_data
def load_classified_catalog():
    return {
        "Popular Choices 熱門選擇": {
            "1": "images/1_neon lights creating a city atmosphere copy.png",
            "2": "images/2_landscape_Anonymous Artist_1925-1928.png",
            "3": "images/3_sunset sail w beach a1_proof.png",
            "4": "images/4_sunset sail ocean.png",
            "5": "images/5_sunset beach.png",
            "6": "images/6_daytime beach.png",
            "7": "images/7_blue sky and sea with yault_app.png",
            "9": "images/9_abstract cat 5.png",
            "10": "images/10_waterfall in greenary floral landscape with sunlight_app.png",
            "11": "images/11_abstract duck 2.png",
            "12": "images/12_colorful cityscape at daytime 50x70cm.png",
            "13": "images/13_colorful cityscape at sunset_app.png",
            "14": "images/14_vintage nature greenary 1_24x36 inches_ratio_2x3.png",
            "15": "images/15_abstract cat 1.png",
            "16": "images/16_abstract cat 4.png",
            "17": "images/17_colorful dog water color 1 _ratio 2x3.png",
            "18": "images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "19": "images/19_walking in the rain_4_40x50cm.png",
            "20": "images/20_minimalist line art of wildflowers.png",
            "21": "images/21_blue bird in floral_40x50cm.png",
            "22": "images/22_colorful cat water color 2 _ratio 2x3.png",
            "23": "images/23_lake and lotus in sun.png",
            "24": "images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
            "25": "images/25_allegory_of_painting_1946.7.png",
        },
        "Masterpieces 名作": {
            "2": "images/2_landscape_Anonymous Artist_1925-1928.png",
            "24": "images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
            "25": "images/25_allegory_of_painting_1946.7.png",
        },
        "Minimalist 簡約": {
            "18": "images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "20": "images/20_minimalist line art of wildflowers.png",
        },
        "Abstract 抽象": {},
        "Nature 自然": {
            "2": "images/2_landscape_Anonymous Artist_1925-1928.png",
            "3": "images/3_sunset sail w beach a1_proof.png",
            "4": "images/4_sunset sail ocean.png",
            "5": "images/5_sunset beach.png",
            "6": "images/6_daytime beach.png",
            "7": "images/7_blue sky and sea with yault_app.png",
            "10": "images/10_waterfall in greenary floral landscape with sunlight_app.png",
            "14": "images/14_vintage nature greenary 1_24x36 inches_ratio_2x3.png",
            "18": "images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "20": "images/20_minimalist line art of wildflowers.png",
            "23": "images/23_lake and lotus in sun.png",
            "24": "images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
        },
        "City 城市": {
            "1": "images/1_neon lights creating a city atmosphere copy.png",
            "12": "images/12_colorful cityscape at daytime 50x70cm.png",
            "13": "images/13_colorful cityscape at sunset_app.png",
            "19": "images/19_walking in the rain_4_40x50cm.png",
        },
        "Animals 動物": {
            "9": "images/9_abstract cat 5.png",
            "11": "images/11_abstract duck 2.png",
            "15": "images/15_abstract cat 1.png",
            "16": "images/16_abstract cat 4.png",
            "17": "images/17_colorful dog water color 1 _ratio 2x3.png",
            "21": "images/21_blue bird in floral_40x50cm.png",
            "22": "images/22_colorful cat water color 2 _ratio 2x3.png",
        },
    }

def sanitize_and_validate_path(base_dir: str, target_path: str) -> bool:
    """Prevents Path Traversal vulnerability by enforcing target directory boundaries."""
    try:
        resolved_base = os.path.realpath(base_dir)
        resolved_target = os.path.realpath(target_path)
        return resolved_target.startswith(resolved_base)
    except Exception:
        return False

def validate_uploaded_file(file_obj) -> bool:
    """Checks size limit and valid extension prior to processing."""
    if file_obj.size > MAX_UPLOAD_SIZE_BYTES:
        st.error(
            f"⚠️ 檔案過大 / File too large! "
            f"請上傳小於 {MAX_UPLOAD_SIZE_MB}MB 的照片 (您的檔案大小: {file_obj.size / (1024 * 1024):.2f}MB)。"
        )
        return False

    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        st.error("❌ 無效的檔案類型 / Invalid file type. Only JPG, PNG, and WebP are allowed.")
        return False

    return True

# ==============================================================================
# 3. STEP 1 PAGE: UPLOAD WALL & SELECT ART
# ==============================================================================
if st.session_state.step == 1:
    st.write("步驟 1：上傳牆面照片，並選擇喜歡的藝術款式 | Step 1: Upload room photo & choose art piece.")

    uploaded_wall = st.file_uploader(
        "1. 上傳牆面照片 / Upload your wall photo",
        type=["jpg", "jpeg", "png", "webp"],
    )
    st.caption("🔒 **隱私安全保障 / Your Privacy Matters:** 上傳的照片僅用於即時效果預覽。")

    if uploaded_wall and validate_uploaded_file(uploaded_wall):
        try:
            raw_wall_img = Image.open(uploaded_wall).convert("RGBA")
            wall_img = ImageOps.exif_transpose(raw_wall_img)

            # Strip EXIF metadata to maintain user privacy
            clean_wall_data = list(wall_img.getdata())
            sanitized_wall = Image.new(wall_img.mode, wall_img.size)
            sanitized_wall.putdata(clean_wall_data)

            # Resize down to prevent memory strain
            if sanitized_wall.width > MAX_IMAGE_WIDTH:
                w_percent = MAX_IMAGE_WIDTH / float(sanitized_wall.width)
                h_size = int(float(sanitized_wall.height) * float(w_percent))
                sanitized_wall = sanitized_wall.resize(
                    (MAX_IMAGE_WIDTH, h_size), Image.Resampling.LANCZOS
                )

            st.session_state.sanitized_wall_img = sanitized_wall

            st.markdown("---")
            st.subheader("2. 選擇藝術款式 / Choose Art Style")

            full_catalog = load_classified_catalog()
            categories = list(full_catalog.keys())
            tabs = st.tabs(categories)

            for i, cat_name in enumerate(categories):
                with tabs[i]:
                    sub_catalog = full_catalog[cat_name]
                    if not sub_catalog:
                        st.info("🎨 即將推出！Coming Soon.")
                    else:
                        items = list(sub_catalog.items())
                        for row_idx in range(0, len(items), 3):
                            row_items = items[row_idx : row_idx + 3]
                            cols = st.columns(3)
                            for col_idx, (art_name, art_path) in enumerate(row_items):
                                with cols[col_idx]:
                                    if sanitize_and_validate_path("images", art_path) and os.path.exists(art_path):
                                        st.image(art_path, use_container_width=True)
                                        
                                        button_label = (
                                            f"✨ 選擇 {art_name[:12]}..."
                                            if len(art_name) > 12
                                            else f"✨ 選擇 {art_name}"
                                        )
                                        
                                        # On click, store state and trigger page transition
                                        if st.button(
                                            button_label,
                                            key=f"btn_{cat_name}_{art_path}_{row_idx}_{col_idx}",
                                            use_container_width=True,
                                        ):
                                            st.session_state.selected_art_path = art_path
                                            st.session_state.selected_art_name = art_name
                                            st.session_state.step = 2
                                            st.rerun()

        except Exception:
            st.error("⚠️ 無法讀取該圖片檔，請上傳有效的 JPG、PNG 或 WebP 圖片。")

# ==============================================================================
# 4. STEP 2 PAGE: PREVIEW & RESIZE ADJUSTMENT
# ==============================================================================
elif st.session_state.step == 2:
    st.write("步驟 2：調整畫作位置與尺寸並預覽效果 | Step 2: Adjust position, size, and preview.")

    wall_img = st.session_state.sanitized_wall_img
    decor_path = st.session_state.selected_art_path

    if wall_img and decor_path and sanitize_and_validate_path("images", decor_path) and os.path.exists(decor_path):
        try:
            with Image.open(decor_path) as d_img:
                decor_img = d_img.convert("RGBA")

            col_controls, col_preview = st.columns([1, 2])

            with col_controls:
                st.subheader("🛠️ 調整選項目錄 / Controls")
                st.markdown(f"**當前選擇 / Art Selected:**\n`{st.session_state.selected_art_name}`")
                st.markdown("---")

                pos_x = st.slider(
                    "左右位置 (X Position)",
                    0,
                    wall_img.width,
                    int(wall_img.width / 3),
                )
                pos_y = st.slider(
                    "上下位置 (Y Position)",
                    0,
                    wall_img.height,
                    int(wall_img.height / 3),
                )
                scale_percent = st.slider(
                    "尺寸大小 (Scale Size %)", 10, 100, 30
                )

                st.markdown("---")

                # Dimensional calculations
                new_w = max(1, int(wall_img.width * (scale_percent / 100.0)))
                aspect_ratio = decor_img.height / decor_img.width
                new_h = max(1, int(new_w * aspect_ratio))

                resized_decor = decor_img.resize(
                    (new_w, new_h), Image.Resampling.LANCZOS
                )
                combined_preview = wall_img.copy()

                # Boundary & crop calculations
                x_start = max(0, pos_x)
                y_start = max(0, pos_y)
                x_end = min(wall_img.width, x_start + new_w)
                y_end = min(wall_img.height, y_start + new_h)

                decor_w_crop = x_end - x_start
                decor_h_crop = y_end - y_start

                if decor_w_crop > 0 and decor_h_crop > 0:
                    cropped_decor = resized_decor.crop(
                        (0, 0, decor_w_crop, decor_h_crop)
                    )
                    combined_preview.alpha_composite(
                        cropped_decor, (x_start, y_start)
                    )

                img_buffer = io.BytesIO()
                final_rgb = combined_preview.convert("RGB")
                final_rgb.save(img_buffer, format="JPEG", quality=95)
                byte_data = img_buffer.getvalue()

                st.download_button(
                    label="💾 下載我的設計 / Download Room Design",
                    data=byte_data,
                    file_name="artprintbuddies_design.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                    type="primary",
                )

                st.write("")
                if st.button(
                    "🔄 重選牆面或畫作 / Back to Step 1",
                    use_container_width=True,
                ):
                    st.session_state.step = 1
                    st.rerun()

            with col_preview:
                st.subheader("👁️ 牆面預覽 / Wall Preview")
                st.image(combined_preview, use_container_width=True)

        except Exception:
            st.error("⚠️ 預覽時發生錯誤，請稍後再試。An unexpected error occurred during preview.")
    else:
        st.warning("⚠️ 數據遺失，請返回第一步上傳照片。Data missing, please go back to step 1.")
        if st.button("返回第一步 / Back to Step 1"):
            st.session_state.step = 1
            st.rerun()

# --- FOOTER ---
st.markdown("---")
col_space1, col_btn, col_space2 = st.columns([1, 1, 1])
with col_btn:
    st.link_button(
        "🛍️ 點擊前往網店選購 / Visit Our Shop",
        "https://artprintbuddies.myshopify.com/",
        use_container_width=True,
    )

st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem; margin-top: 15px;'>"
    "© 2026 ArtPrintBuddies 圖畫裝飾 (Tung Fong Printing Service 東方晒圖). All Rights Reserved."
    "</p>",
    unsafe_allow_html=True,
)
