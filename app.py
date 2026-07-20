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
