import io
import os
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import streamlit as st

# --- 1. SECURITY & MEMORY SAFEGUARDS ---
MAX_PIXEL_COUNT = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXEL_COUNT

MAX_IMAGE_WIDTH = 1200
MAX_UPLOAD_SIZE_MB = 3
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

st.set_page_config(page_title="ArtPrintBuddies Visualizer", layout="wide")

# Custom CSS focused on mobile height-compactness
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    div[data-testid="stSlider"] {
        margin-bottom: -10px;
    }
    
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }

    div[data-testid="column"] {
        padding: 0 4px !important;
    }
    
    button {
        border-radius: 8px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE INITIALIZATION ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "sanitized_wall_img" not in st.session_state:
    st.session_state.sanitized_wall_img = None
if "selected_art_path" not in st.session_state:
    st.session_state.selected_art_path = None
if "selected_art_name" not in st.session_state:
    st.session_state.selected_art_name = None

# --- BRANDING & SIDEBAR ---
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

st.title("🎨 ArtPrintBuddies Visualizer")

# ==============================================================================
# 2. HELPER UTILITIES
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
    try:
        resolved_base = os.path.realpath(base_dir)
        resolved_target = os.path.realpath(target_path)
        return resolved_target.startswith(resolved_base)
    except Exception:
        return False

def validate_uploaded_file(file_obj) -> bool:
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

def draw_option_label_on_image(pil_image: Image.Image, text: str) -> Image.Image:
    """Draws a neat dark overlay box with white text in the top-left corner."""
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
    
    label_text = f"Art: {text}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, img_cv.shape[1] / 1500.0)
    thickness = max(1, int(font_scale * 2))
    
    (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
    
    # Overlay box dimensions
    padding = 10
    box_x1, box_y1 = 15, 15
    box_x2, box_y2 = box_x1 + text_w + (padding * 2), box_y1 + text_h + (padding * 2)
    
    # Create semi-transparent dark rectangle background
    overlay = img_cv.copy()
    cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (0, 0, 0, 180), -1)
    cv2.addWeighted(overlay, 0.6, img_cv, 0.4, 0, img_cv)
    
    # Draw text inside box
    text_org = (box_x1 + padding, box_y1 + text_h + padding - 2)
    cv2.putText(img_cv, label_text, text_org, font, font_scale, (255, 255, 255, 255), thickness, cv2.LINE_AA)
    
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGRA2RGBA))

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

            clean_wall_data = list(wall_img.getdata())
            sanitized_wall = Image.new(wall_img.mode, wall_img.size)
            sanitized_wall.putdata(clean_wall_data)

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
# 4. STEP 2 PAGE: COMPACT PREVIEW & INSTRUCTIONS
# ==============================================================================
elif st.session_state.step == 2:
    wall_img = st.session_state.sanitized_wall_img
    decor_path = st.session_state.selected_art_path

    if wall_img and decor_path and sanitize_and_validate_path("images", decor_path) and os.path.exists(decor_path):
        try:
            with Image.open(decor_path) as d_img:
                decor_img = d_img.convert("RGBA")

            # --- 1. CONTROLS WITH ENGLISH & CHINESE INSTRUCTIONS ---
            col_x, col_y = st.columns(2)
            with col_x:
                pos_x = st.slider(
                    "↔️ 左右位置 (X Position)",
                    0,
                    wall_img.width,
                    int(wall_img.width / 3),
                    help="Drag left/right to shift artwork horizontally. 左右拖動可移動畫作水平位置。"
                )
            with col_y:
                pos_y = st.slider(
                    "↕️ 上下位置 (Y Position)",
                    0,
                    wall_img.height,
                    int(wall_img.height / 3),
                    help="Drag up/down to adjust artwork height on wall. 上下拖動可調整畫作掛牆高度。"
                )

            scale_percent = st.slider(
                "🔍 畫作尺寸 (Artwork Size %)", 
                10, 
                100, 
                30,
                help="Slide to make artwork larger or smaller. 拖動滑塊即可放大或縮小畫作尺寸。"
            )

            # --- 2. COMPOSITE CALCULATION ---
            new_w = max(1, int(wall_img.width * (scale_percent / 100.0)))
            aspect_ratio = decor_img.height / decor_img.width
            new_h = max(1, int(new_w * aspect_ratio))

            resized_decor = decor_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            combined_preview = wall_img.copy()

            x_start = max(0, pos_x)
            y_start = max(0, pos_y)
            x_end = min(wall_img.width, x_start + new_w)
            y_end = min(wall_img.height, y_start + new_h)

            decor_w_crop = x_end - x_start
            decor_h_crop = y_end - y_start

            if decor_w_crop > 0 and decor_h_crop > 0:
                cropped_decor = resized_decor.crop((0, 0, decor_w_crop, decor_h_crop))
                combined_preview.alpha_composite(cropped_decor, (x_start, y_start))

            # --- 3. OVERLAY OPTION NAME IN CORNER ---
            final_preview = draw_option_label_on_image(
                combined_preview, 
                st.session_state.selected_art_name
            )

            st.image(final_preview, use_container_width=True)

            # --- 4. ACTION BUTTONS ---
            img_buffer = io.BytesIO()
            final_rgb = final_preview.convert("RGB")
            final_rgb.save(img_buffer, format="JPEG", quality=95)
            byte_data = img_buffer.getvalue()

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button(
                    label="💾 下載設計 (Download Design)",
                    data=byte_data,
                    file_name=f"design_art_{st.session_state.selected_art_name}.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                    type="primary",
                )
            with btn_col2:
                if st.button("🔄 重選 (Back)", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()

        except Exception:
            st.error("⚠️ 預覽時發生錯誤，請稍後再試。An unexpected error occurred during preview.")
    else:
        st.warning("⚠️ 數據遺失，請返回第一步上傳照片。Data missing, please go back to step 1.")
        if st.button("返回第一步 / Back to Step 1"):
            st.session_state.step = 1
            st.rerun()

# --- FOOTER ---
st.markdown("---")
st.link_button(
    "🛍️ 點擊前往網店選購 / Visit Our Shop",
    "https://artprintbuddies.myshopify.com/",
    use_container_width=True,
)

st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem; margin-top: 10px;'>"
    "© 2026 ArtPrintBuddies 圖畫裝飾 (Tung Fong Printing Service 東方晒圖). All Rights Reserved."
    "</p>",
    unsafe_allow_html=True,
)
