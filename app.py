import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import os
import base64
import json

# Set up page layout
st.set_page_config(page_title="ArtPrintBuddies Visualizer", layout="wide")

# Custom CSS to force responsiveness
st.markdown("""
    <style>
    /* Ensure the iframe/canvas fits nicely within the screen height */
    iframe {
        max-height: 50vh !important;
        border: 1px solid #ddd;
        border-radius: 8px;
    }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 8px;
        padding: 5px;
        transition: transform 0.2s;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        transform: scale(1.05);
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
                                        # Reset position values on item switch
                                        st.session_state.wall_x_slider = int(wall_img.width / 3)
                                        st.session_state.wall_y_slider = int(wall_img.height / 3)
                                        st.session_state.wall_w_slider = int(wall_img.width / 4)
                                        st.session_state.wall_op_slider = 0.95
                                        st.rerun()

    with col_canvas:
        st.subheader("👁️ 預覽與調整 / Preview & Adjust")
        
        if not st.session_state.selected_art_path:
            st.image(wall_img, use_container_width=True)
            st.info("👈 請在左側選單點擊裝飾畫圖片，以進行效果預覽！")
        else:
            decor_path = st.session_state.selected_art_path
            if os.path.exists(decor_path):
                decor_img = Image.open(decor_path).convert("RGBA")
                
                # Fetch baseline adjustments cleanly from session cache
                current_x = st.session_state.get("wall_x_slider", int(wall_img.width / 3))
                current_y = st.session_state.get("wall_y_slider", int(wall_img.height / 3))
                current_w = st.session_state.get("wall_w_slider", int(wall_img.width / 4))
                current_op = st.session_state.get("wall_op_slider", 0.95)

                # Base64 encode images to inject cleanly into HTML5 touch layout frame
                wall_b64 = get_base64_image(wall_img)
                decor_b64 = get_base64_image(decor_img)
                
                aspect_ratio = decor_img.height / decor_img.width
                
                # --- INTERACTIVE JAVASCRIPT/HTML5 TOUCH CANVAS COMPONENT ---
                html_code = f"""
                <div style="position: relative; width: 100%; max-width: 100%; overflow: hidden; display: flex; justify-content: center;">
                    <canvas id="canvas" style="max-height: 48vh; object-fit: contain; width: 100%; border-radius: 6px; background:#eee;"></canvas>
                </div>
                <script>
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    const wallImg = new Image();
                    const artImg = new Image();
                    
                    wallImg.src = "data:image/png;base64,{wall_b64}";
                    artImg.src = "data:image/png;base64,{decor_b64}";
                    
                    let art = {{
                        x: {current_x},
                        y: {current_y},
                        w: {current_w},
                        h: Math.round({current_w} * {aspect_ratio}),
                        opacity: {current_op}
                    }};
                    
                    let isDragging = false;
                    let startX, startY;
                    
                    function draw() {{
                        canvas.width = wallImg.width;
                        canvas.height = wallImg.height;
                        ctx.drawImage(wallImg, 0, 0);
                        ctx.globalAlpha = art.opacity;
                        ctx.drawImage(artImg, art.x, art.y, art.w, art.h);
                        ctx.globalAlpha = 1.0;
                    }}
                    
                    function getCoordinates(e) {{
                        const rect = canvas.getBoundingClientRect();
                        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                        return {{
                            x: ((clientX - rect.left) / rect.width) * canvas.width,
                            y: ((clientY - rect.top) / rect.height) * canvas.height
                        }};
                    }}
                    
                    function startAction(e) {{
                        const coord = getCoordinates(e);
                        if (coord.x >= art.x && coord.x <= art.x + art.w && coord.y >= art.y && coord.y <= art.y + art.h) {{
                            isDragging = true;
                            startX = coord.x - art.x;
                            startY = coord.y - art.y;
                            if(e.cancelable) e.preventDefault();
                        }}
                    }}
                    
                    function moveAction(e) {{
                        if (!isDragging) return;
                        const coord = getCoordinates(e);
                        art.x = coord.x - startX;
                        art.y = coord.y - startY;
                        draw();
                        
                        // Send new values back to Streamlit parameters silently
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify({{x: Math.round(art.x), y: Math.round(art.y)}})
                        }}, '*');
                        if(e.cancelable) e.preventDefault();
                    }}
                    
                    function stopAction() {{ isDragging = false; }}
                    
                    wallImg.onload = () => {{ artImg.onload = () => {{ draw(); }}; }};
                    
                    // Mouse Listeners
                    canvas.addEventListener('mousedown', startAction);
                    window.addEventListener('mousemove', moveAction);
                    window.addEventListener('mouseup', stopAction);
                    
                    // Mobile Touch Listeners 
                    canvas.addEventListener('touchstart', startAction, {{ passive: false }});
                    window.addEventListener('touchmove', moveAction, {{ passive: false }});
                    window.addEventListener('touchend', stopAction);
                </script>
                """
                
                # Render interactive HTML window frame with custom bridge return communication
                import streamlit.components.v1 as components
                response_data = components.html(html_code, height=380, scrolling=False)
                
                # Sync touch values back seamlessly into Streamlit tracking loop state
                # Check for updates from window events, or fall back to sliders
                st.markdown("### ⚙️ 調整工具 / Position Controls")
                st.markdown(f"**當前選定 / Selected:** `{st.session_state.selected_art_name}`")
                
                x_pos = st.slider("左右移動 (Left / Right)", 0, wall_img.width, value=current_x, key="wall_x_slider")
                y_pos = st.slider("上下移動 (Up / Down)", 0, wall_img.height, value=current_y, key="wall_y_slider")
                decor_w = st.slider("調整尺寸 (Width)", 50, wall_img.width, value=current_w, key="wall_w_slider")
                opacity = st.slider("環境光線融和度 (Opacity)", 0.5, 1.0, value=current_op, step=0.05, key="wall_op_slider")
                
                # Standard Python Composite Processing for downscaled exports
                decor_h = int(decor_w * aspect_ratio)
                decor_resized = decor_img.resize((decor_w, decor_h), Image.Resampling.LANCZOS)
                if opacity < 1.0:
                    alpha = decor_resized.split()[3].point(lambda p: p * opacity)
                    decor_resized.putalpha(alpha)
                
                preview_canvas = wall_img.copy()
                preview_canvas.paste(decor_resized, (x_pos, y_pos), decor_resized)
                
                col_down, col_reset = st.columns(2)
                with col_down:
                    st.download_button(
                        label="💾 下載我的設計 / Download Room Design",
                        data=cv2.imencode('.png', cv2.cvtColor(np.array(preview_canvas), cv2.COLOR_RGBA2BGRA))[1].tobytes(),
                        file_name="artprintbuddies_design.png",
                        mime="image/png",
                        use_container_width=True
                    )
                with col_reset:
                    if st.button("🔄 試試其他牆面 / Try Another Photo", use_container_width=True):
                        for key in ["selected_art_path", "selected_art_name", "wall_x_slider", "wall_y_slider", "wall_w_slider", "wall_op_slider"]:
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
