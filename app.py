import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import os
import io

# Set up page layout
st.set_page_config(page_title="ArtPrintBuddies Visualizer", layout="wide")

# Custom CSS to force clean mobile stacking and button hover actions
st.markdown("""
    <style>
    /* Break side-by-side layout into single columns on small screen viewports */
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
    
    /* Make the slider element look nice and prominent */
    div[data-element-to-test="stMarkdownContainer"] {
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- BRANDING & SIDEBAR COMPANY DETAILS ---
with st.sidebar:
    st.markdown("# 🖼️ ArtPrintBuddies")
    st.markdown("### 圖畫裝飾")
    st.caption("Powered by Tung Fong Printing Service 東方晒圖")
    st.markdown("---")
    st.write("室內效果預覽工具：上傳您的房間照片，即可模擬裝飾畫掛牆效果。")
    st.write("Upload a photo of your room to see how our decor looks on your wall!")
    st.markdown("---")

st.title("🎨 ArtPrintBuddies Wall Art Visualizer")
st.write("模擬您的專屬藝術牆面 | Preview your custom prints instantly.")

MAX_IMAGE_WIDTH = 1200

@st.cache_data
def load_classified_catalog():
    return {
        "Popular Choices 熱門選擇": {
            "1":"images/1_neon lights creating a city atmosphere copy.png",
            "2":"images/2_landscape_Anonymous Artist_1925-1928.png",
            "3":"images/3_sunset sail w beach a1_proof.png",
            "4":"images/4_sunset sail ocean.png",
            "5":"images/5_sunset beach.png",
            "6":"images/6_daytime beach.png",
            "7":"images/7_blue sky and sea with yault_app.png",
            "9":"images/9_abstract cat 5.png",
            "10":"images/10_waterfall in greenary floral landscape with sunlight_app.png",
            "11":"images/11_abstract duck 2.png",
            "12":"images/12_colorful cityscape at daytime 50x70cm.png",
            "13":"images/13_colorful cityscape at sunset_app.png",
            "14":"images/14_vintage nature greenary 1_24x36 inches_ratio_2x3.png",
            "15":"images/15_abstract cat 1.png",
            "16":"images/16_abstract cat 4.png",
            "17":"images/17_colorful dog water color 1 _ratio 2x3.png",
            "18":"images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "19":"images/19_walking in the rain_4_40x50cm.png",
            "20":"images/20_minimalist line art of wildflowers.png",
            "21":"images/21_blue bird in floral_40x50cm.png",
            "22":"images/22_colorful cat water color 2 _ratio 2x3.png",
            "23":"images/23_lake and lotus in sun.png",
            "24":"images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
            "25":"images/25_allegory_of_painting_1946.7.png",
        },
        "Masterpieces 名作": {
            "2":"images/2_landscape_Anonymous Artist_1925-1928.png",
            "24":"images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
            "25":"images/25_allegory_of_painting_1946.7.png"
        },
        "Minimalist 簡約": {
            "18":"images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "20":"images/20_minimalist line art of wildflowers.png"
        },
        "Abstract 抽象":{},
        "Nature 自然": {
            "2":"images/2_landscape_Anonymous Artist_1925-1928.png",
            "3":"images/3_sunset sail w beach a1_proof.png",
            "4":"images/4_sunset sail ocean.png",
            "5":"images/5_sunset beach.png",
            "6":"images/6_daytime beach.png",
            "7":"images/7_blue sky and sea with yault_app.png",
            "10":"images/10_waterfall in greenary floral landscape with sunlight_app.png",
            "14":"images/14_vintage nature greenary 1_24x36 inches_ratio_2x3.png",
            "18":"images/18_minimalist botanical line drawing of eucalyptus branches.png",
            "20":"images/20_minimalist line art of wildflowers.png",
            "23":"images/23_lake and lotus in sun.png",
            "24":"images/24 wooded_landscape_with_figures_Meindert Hobbema_c1658.png",
        },
        "City 城市": {
            "1":"images/1_neon lights creating a city atmosphere copy.png",
            "12":"images/12_colorful cityscape at daytime 50x70cm.png",
            "13":"images/13_colorful cityscape at sunset_app.png",
            "19":"images/19_walking in the rain_4_40x50cm.png",
        },
        "Animals 動物": {
            "9":"images/9_abstract cat 5.png",
            "11":"images/11_abstract duck 2.png",
            "15":"images/15_abstract cat 1.png",
            "16":"images/16_abstract cat 4.png",
            "17":"images/17_colorful dog water color 1 _ratio 2x3.png",
            "21":"images/21_blue bird in floral_40x50cm.png",
            "22":"images/22_colorful cat water color 2 _ratio 2x3.png", 
        }
    }

# --- MAIN SCREEN: UPLOAD WALL ---
uploaded_wall = st.file_uploader("1. 上傳牆面照片 / Upload your wall photo", type=["jpg", "jpeg", "png", "webp"])
st.caption("🔒 **隱私安全保障 / Your Privacy Matters:** 上傳的照片僅用於即時效果預覽。")

if uploaded_wall:
    raw_wall_img = Image.open(uploaded_wall).convert("RGBA")
    wall_img = ImageOps.exif_transpose(raw_wall_img)
    
    # Scale width down gently to save processing memory while keeping native vertical layout intact
    if wall_img.width > MAX_IMAGE_WIDTH:
        w_percent = MAX_IMAGE_WIDTH / float(wall_img.width)
        h_size = int(float(wall_img.height) * float(w_percent))
        wall_img = wall_img.resize((MAX_IMAGE_WIDTH, h_size), Image.Resampling.LANCZOS)

    col_gallery, col_canvas = st.columns([1, 1])

    with col_gallery:
        st.subheader("🎨 選擇藝術款式 / Choose Art Style")
        full_catalog = load_classified_catalog()
        categories = list(full_catalog.keys())
        
        if "selected_art_path" not in st.session_state:
            st.session_state.selected_art_path = None
        if "selected_art_name" not in st.session_state:
            st.session_state.selected_art_name = None

        tabs = st.tabs(categories)
        for i, cat_name in enumerate(categories):
            with tabs[i]:
                sub_catalog = full_catalog[cat_name]
                if not sub_catalog:
                    st.info("🎨 即將推出！Coming Soon.")
                else:
                    items = list(sub_catalog.items())
                    for row_idx in range(0, len(items), 3):
                        row_items = items[row_idx:row_idx+3]
                        cols = st.columns(3)
                        for col_idx, (art_name, art_path) in enumerate(row_items):
                            with cols[col_idx]:
                                if os.path.exists(art_path):
                                    st.image(Image.open(art_path), use_container_width=True)
                                    button_label = f"✨ {art_name[:12]}..." if len(art_name) > 12 else f"✨ {art_name}"
                                    if st.button(button_label, key=f"btn_{cat_name}_{art_path}_{row_idx}_{col_idx}", use_container_width=True):
                                        st.session_state.selected_art_path = art_path
                                        st.session_state.selected_art_name = art_name
                                        st.rerun()

    with col_canvas:
        st.subheader("👁️ 預覽與調整 / Preview & Adjust")
        
        if not st.session_state.selected_art_path:
            # Displays natively through Streamlit without any framework cropping rules
            st.image(wall_img, use_container_width=True)
            st.info("👈 請在左側選單點擊裝飾畫圖片，以進行效果預覽！")
        else:
            decor_path = st.session_state.selected_art_path
            if os.path.exists(decor_path):
                decor_img = Image.open(decor_path).convert("RGBA")
                
                st.write("🛠️ **調整畫作位置與大小 / Controls:**")
                
                # Dynamic adjustment sliders powered completely natively by Streamlit backend
                col_x, col_y = st.columns(2)
                with col_x:
                    pos_x = st.slider("左右位置 (X Position)", 0, wall_img.width, int(wall_img.width / 3))
                with col_y:
                    pos_y = st.slider("上下位置 (Y Position)", 0, wall_img.height, int(wall_img.height / 3))
                    
                scale_percent = st.slider("尺寸大小 (Scale Size %)", 10, 100, 30)

                # Use Python logic to blend the images safely 
                # Calculate new sizes based on user sliders
                new_w = int(wall_img.width * (scale_percent / 100.0))
                aspect_ratio = decor_img.height / decor_img.width
                new_h = int(new_w * aspect_ratio)
                
                resized_decor = decor_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Make a workspace copy of our base wall image
                combined_preview = wall_img.copy()
                
                # Safeguard clipping bounding box coordinates to keep layers safely on image canvas
                x_start = max(0, pos_x)
                y_start = max(0, pos_y)
                x_end = min(wall_img.width, x_start + new_w)
                y_end = min(wall_img.height, y_start + new_h)
                
                # Calculate crop size for art if it hangs off the background edge boundaries
                decor_w_crop = x_end - x_start
                decor_h_crop = y_end - y_start
                
                if decor_w_crop > 0 and decor_h_crop > 0:
                    cropped_decor = resized_decor.crop((0, 0, decor_w_crop, decor_h_crop))
                    # Alpha compositing blend execution loop
                    combined_preview.alpha_composite(cropped_decor, (x_start, y_start))
                
                # Render the combined composition natively without an iframe wrapper
                st.image(combined_preview, use_container_width=True)
                st.markdown(f"**當前選定 / Selected:** `{st.session_state.selected_art_name}`")
                
                # Turn image matrix into file data streams for the download button
                img_buffer = io.BytesIO()
                # Convert back to RGB for crisp JPEG exports
                final_rgb = combined_preview.convert("RGB")
                final_rgb.save(img_buffer, format="JPEG", quality=95)
                byte_data = img_buffer.getvalue()
                
                # Standard Streamlit Download Button - Always 100% visible, cannot be hidden!
                st.download_button(
                    label="💾 下載我的設計 / Download Room Design",
                    data=byte_data,
                    file_name="artprintbuddies_design.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                    type="primary"
                )
                
                st.write("") # Spacer row
                if st.button("🔄 試試其他牆面 / Try Another Photo", use_container_width=True):
                    for key in ["selected_art_path", "selected_art_name"]:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

# --- FOOTER WITH COPYRIGHT & SHOPIFY BUTTON ---
st.markdown("---")
col_space1, col_btn, col_space2 = st.columns([1, 1, 1])
with col_btn:
    st.link_button("🛍️ 點擊前往網店選購 / Visit Our Shop", "https://artprintbuddies.myshopify.com/", use_container_width=True)

st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem; margin-top: 15px;'>"
    "© 2026 ArtPrintBuddies 圖畫裝飾 (Tung Fong Printing Service 東方晒圖). All Rights Reserved."
    "</p>", unsafe_allow_html=True
)
