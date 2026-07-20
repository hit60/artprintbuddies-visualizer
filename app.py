import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import os
import base64

# Set up page layout
st.set_page_config(page_title="ArtPrintBuddies Visualizer", layout="wide")

# Custom CSS to force clean mobile stacking and responsive uncropped preview boxes
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
    
    /* Completely unlock the iframe frame container to scale natively without clipping lines */
    iframe {
        width: 100% !important;
        height: auto !important;
        border: 2px solid #e6e9ef;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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

def get_base64_image(img):
    import io
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- MAIN SCREEN: UPLOAD WALL ---
uploaded_wall = st.file_uploader("1. 上傳牆面照片 / Upload your wall photo", type=["jpg", "jpeg", "png", "webp"])
st.caption("🔒 **隱私安全保障 / Your Privacy Matters:** 上傳的照片僅用於即時效果預覽。")

if uploaded_wall:
    raw_wall_img = Image.open(uploaded_wall).convert("RGBA")
    wall_img = ImageOps.exif_transpose(raw_wall_img)
    
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
            st.image(wall_img, use_container_width=True)
            st.info("👈 請在上方或左側選單點擊裝飾畫圖片，以進行效果預覽！")
        else:
            decor_path = st.session_state.selected_art_path
            if os.path.exists(decor_path):
                decor_img = Image.open(decor_path).convert("RGBA")
                aspect_ratio = decor_img.height / decor_img.width
                
                init_x = int(wall_img.width / 3)
                init_y = int(wall_img.height / 3)
                init_w = int(wall_img.width / 4)

                wall_b64 = get_base64_image(wall_img)
                decor_b64 = get_base64_image(decor_img)

                # --- UNCACHED NATIVE SCALE RATIO INTERACTIVE CONTAINER WINDOW ---
                html_code = f"""
                <div style="width: 100%; display: flex; flex-direction: column; align-items: center; gap: 15px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; box-sizing: border-box; padding: 5px;">
                    <canvas id="canvas" style="width: 100%; max-width: 100%; height: auto; aspect-ratio: {wall_img.width}/{wall_img.height}; background: #fafafa; border-radius: 8px; touch-action: none; border: 1px solid #ddd; box-sizing: border-box; display: block;"></canvas>
                    
                    <button id="dlBtn" style="width: 100%; background-color: #ff4b4b; color: white; border: none; padding: 14px 24px; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: background 0.2s;">
                        💾 下載我的設計 / Download Room Design
                    </button>
                </div>

                <script>
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    const dlBtn = document.getElementById('dlBtn');
                    
                    const wallImg = new Image();
                    const artImg = new Image();
                    
                    wallImg.src = "data:image/png;base64,{wall_b64}";
                    artImg.src = "data:image/png;base64,{decor_b64}";
                    
                    let art = {{
                        x: {init_x},
                        y: {init_y},
                        w: {init_w},
                        h: Math.round({init_w} * {aspect_ratio})
                    }};
                    
                    let isDragging = false;
                    let startX, startY;
                    let initTouchDist = 0;
                    let initArtW = 0;
                    
                    function draw() {{
                        canvas.width = wallImg.width;
                        canvas.height = wallImg.height;
                        ctx.drawImage(wallImg, 0, 0);
                        ctx.drawImage(artImg, art.x, art.y, art.w, art.h);
                    }}
                    
                    function getCoordinates(clientX, clientY) {{
                        const rect = canvas.getBoundingClientRect();
                        return {{
                            x: ((clientX - rect.left) / rect.width) * canvas.width,
                            y: ((clientY - rect.top) / rect.height) * canvas.height
                        }};
                    }}
                    
                    function startAction(clientX, clientY) {{
                        const coord = getCoordinates(clientX, clientY);
                        if (coord.x >= art.x && coord.x <= art.x + art.w && coord.y >= art.y && coord.y <= art.y + art.h) {{
                            isDragging = true;
                            startX = coord.x - art.x;
                            startY = coord.y - art.y;
                        }}
                    }}
                    
                    function moveAction(clientX, clientY) {{
                        if (!isDragging) return;
                        const coord = getCoordinates(clientX, clientY);
                        art.x = coord.x - startX;
                        art.y = coord.y - startY;
                        draw();
                    }}
                    
                    function getTouchDist(touches) {{
                        const dx = touches[0].clientX - touches[1].clientX;
                        const dy = touches[0].clientY - touches[1].clientY;
                        return Math.sqrt(dx*dx + dy*dy);
                    }}
                    
                    canvas.addEventListener('mousedown', (e) => startAction(e.clientX, e.clientY));
                    window.addEventListener('mousemove', (e) => moveAction(e.clientX, e.clientY));
                    window.addEventListener('mouseup', () => isDragging = false);
                    
                    canvas.addEventListener('touchstart', (e) => {{
                        if (e.touches.length === 1) {{
                            startAction(e.touches[0].clientX, e.touches[0].clientY);
                        }} else if (e.touches.length === 2) {{
                            isDragging = false;
                            initTouchDist = getTouchDist(e.touches);
                            initArtW = art.w;
                        }}
                    }}, {{ passive: false }});
                    
                    window.addEventListener('touchmove', (e) => {{
                        if (e.touches.length === 1 && isDragging) {{
                            moveAction(e.touches[0].clientX, e.touches[0].clientY);
                            e.preventDefault();
                        }} else if (e.touches.length === 2) {{
                            const currentDist = getTouchDist(e.touches);
                            const scale = currentDist / initTouchDist;
                            art.w = Math.max(50, Math.min(wallImg.width, Math.round(initArtW * scale)));
                            art.h = Math.round(art.w * {aspect_ratio});
                            draw();
                            e.preventDefault();
                        }}
                    }}, {{ passive: false }});
                    
                    window.addEventListener('touchend', () => {{ isDragging = false; }});
                    
                    canvas.addEventListener('wheel', (e) => {{
                        e.preventDefault();
                        const scaleFactor = e.deltaY < 0 ? 1.05 : 0.95;
                        art.w = Math.max(50, Math.min(wallImg.width, Math.round(art.w * scaleFactor)));
                        art.h = Math.round(art.w * {aspect_ratio});
                        draw();
                    }}, {{ passive: false }});
                    
                    dlBtn.addEventListener('click', () => {{
                        const link = document.createElement('a');
                        link.download = 'artprintbuddies_design.png';
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                    }});
                    
                    wallImg.onload = () => {{ artImg.onload = () => {{ draw(); }}; }};
                </script>
                """
                
                import streamlit.components.v1 as components
                
                # Dynamic height tracking calculation formula
                # Allocates space based on image layout scale + 90px extra headroom buffer for buttons
                wall_ratio = wall_img.height / wall_img.width
                calculated_height = int((600 * wall_ratio) + 90)
                
                # Hard limit bounding range to avoid infinite structural sizing issues
                final_height = max(450, min(calculated_height, 900))
                
                components.html(html_code, height=final_height, scrolling=False)
                
                st.markdown(f"**當前選定 / Selected:** `{st.session_state.selected_art_name}`")
                
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
