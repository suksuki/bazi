
import streamlit.components.v1 as components
import json
import numpy as np
from core.trinity.core.physics.wave_laws import WaveState

def render_wave_vision_3d(waves, full_bazi_context=None, dm_wave=None, resonance=None, injections=None, height=600):
    """
    Quantum Orrery V5.2: The Ultimate Fate Visualization
    ====================================================
    Master Jin's approved standard for high-dimensional destiny visualization.
    
    Features:
    - Binary Neutron Stars (Pillars as Stem-Branch binary systems)
    - Quantum Wave Shells (Concentric wireframe element grids)
    - Fate Breath (Stability-driven pulsing)
    - Chrono-Layering (Natal center, Luck background, Annual comets)
    """
    
    # 1. Prepare Chrono-Data (Binary Stars)
    pillars_data = []
    # Natal 4 (0-3), Luck (4), Annual (5)
    for i in range(min(6, len(full_bazi_context or []))):
        p_str = full_bazi_context[i]
        if not p_str or len(p_str) < 2: continue
        
        p_type = "NATAL"
        if i == 4: p_type = "LUCK"
        if i == 5: p_type = "ANNUAL"
        
        pillars_data.append({
            "type": p_type, "label": p_str, "stem": p_str[0], "branch": p_str[1], "id": i
        })
    
    # In Quantum Lab, luck/annual are separate. We should try to find them.
    # We'll use dummy data if not explicitly passed, but ideally they'd be in a unified context.
    
    # 2. Prepare Element Shells
    elements_data = []
    colors = {
        "Wood": "#4ade80", "Fire": "#f87171", "Earth": "#fdba74", "Metal": "#94a3b8", "Water": "#38bdf8"
    }
    for name, color in colors.items():
        wave = waves.get(name, WaveState(amplitude=0, phase=0))
        elements_data.append({
            "name": name, "color": color, 
            "amplitude": float(wave.amplitude), 
            "phase": float(wave.phase)
        })

    # 3. System Health (Resonance)
    res_data = {
        "mode": resonance.mode if resonance else "DAMPED",
        "sync": resonance.sync_state if resonance else 0.0,
        "brittleness": getattr(resonance, 'brittleness', 0.0)
    }

    data_json = json.dumps({
        "elements": elements_data,
        "pillars": pillars_data,
        "resonance": res_data
    })
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; overflow: hidden; background: #000000; }}
            #container {{ width: 100%; height: {height}px; }}
            #hud {{
                position: absolute; bottom: 20px; right: 20px;
                color: #ff9f43; font-family: 'Courier New', Courier, monospace;
                pointer-events: none; text-align: right;
                border-right: 2px solid #ff9f43; padding-right: 15px;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="hud">
            [ARCHIVE: ORRERY V5.2]<br>
            FIELD: <span id="mode-val">DAMPED</span><br>
            COHERENCE: <span id="sync-val">0.000</span>
        </div>
        <div id="container"></div>
        <script>
            const data = {data_json};
            document.getElementById('mode-val').innerText = data.resonance.mode;
            document.getElementById('sync-val').innerText = data.resonance.sync.toFixed(3);

            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('container').appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            camera.position.set(20, 15, 20);
            controls.enableDamping = true;

            // 1. LIGHTING
            scene.add(new THREE.AmbientLight(0xffffff, 0.2));
            const pLight = new THREE.PointLight(0xffffff, 1, 50);
            pLight.position.set(0, 10, 0);
            scene.add(pLight);

            // 2. QUANTUM WAVE SHELLS (Wireframe Grids)
            const shells = [];
            data.elements.forEach((el, idx) => {{
                if(el.amplitude < 0.1) return;
                
                const radius = 6 + idx * 1.5;
                const geom = new THREE.SphereGeometry(radius, 32, 24);
                const mat = new THREE.MeshBasicMaterial({{
                    color: el.color,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.15
                }});
                const shell = new THREE.Mesh(geom, mat);
                scene.add(shell);
                shells.push({{ mesh: shell, baseRadius: radius, data: el }});
            }});

            // 3. BINARY NEUTRON STARS (Pillars)
            const pillarGroups = [];
            function createCharTexture(char, color) {{
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 128; canvas.height = 128;
                ctx.font = 'bold 90px "Microsoft YaHei"';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(char, 64, 64);
                return new THREE.CanvasTexture(canvas);
            }}

            const starGeo = new THREE.SphereGeometry(0.3, 16, 16);
            
            data.pillars.forEach((p, idx) => {{
                const group = new THREE.Group();
                
                // Position based on type
                if (p.type === "NATAL") {{
                    const angle = (idx / 4) * Math.PI * 2;
                    group.position.set(Math.cos(angle)*5, (Math.random()-0.5)*2, Math.sin(angle)*5);
                }} else if (p.type === "LUCK") {{
                    group.position.set(0, -8, 15); // Static start for luck field
                }} else if (p.type === "ANNUAL") {{
                    group.position.set(20, 10, 0); // Static start for annual comet
                }}
                
                scene.add(group);
                
                // Stem Star
                const sMat = new THREE.MeshPhongMaterial({{ color: 0xffffff, emissive: 0x00ffff, emissiveIntensity: 2 }});
                const stemStar = new THREE.Mesh(starGeo, sMat);
                group.add(stemStar);
                
                // Stem Label
                const sTex = createCharTexture(p.stem, '#ffffff');
                const sSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: sTex }}));
                sSprite.scale.set(1.5, 1.5, 1.5);
                sSprite.position.y = 0.8;
                stemStar.add(sSprite);

                // Branch Star
                const bMat = new THREE.MeshPhongMaterial({{ color: 0x40e0d0, emissive: 0x40e0d0, emissiveIntensity: 1.5 }});
                const branchStar = new THREE.Mesh(starGeo, bMat);
                group.add(branchStar);
                
                // Branch Label
                const bTex = createCharTexture(p.branch, '#40e0d0');
                const bSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: bTex }}));
                bSprite.scale.set(1.8, 1.8, 1.8);
                bSprite.position.y = -0.8;
                branchStar.add(bSprite);
                
                // Light Beam Connection (Elliptic Orbit)
                const curve = new THREE.EllipseCurve(0, 0, 1.2, 1.2, 0, 2 * Math.PI, false, 0);
                const points = curve.getPoints(50);
                const ringGeo = new THREE.BufferGeometry().setFromPoints(points);
                const ringMat = new THREE.LineBasicMaterial({{ color: 0x00ffff, transparent: true, opacity: 0.3 }});
                const orbitRing = new THREE.Line(ringGeo, ringMat);
                orbitRing.rotation.x = Math.PI/2;
                group.add(orbitRing);

                pillarGroups.push({{ 
                    group, 
                    stem: stemStar, 
                    branch: branchStar, 
                    timeOffset: idx * 2.3,
                    type: p.type 
                }});
            }});

            // 4. LUCK FIELD (Background Dust)
            // Enhanced with color temperature shift based on sync
            const dustGeo = new THREE.BufferGeometry();
            const dustPos = [];
            for (let i = 0; i < 3000; i++) {{
                dustPos.push((Math.random()-0.5)*100, (Math.random()-0.5)*100, (Math.random()-0.5)*100);
            }}
            dustGeo.setAttribute('position', new THREE.Float32BufferAttribute(dustPos, 3));
            const dustMat = new THREE.PointsMaterial({{ color: 0x40e0d0, size: 0.15, transparent: true, opacity: 0.3 }});
            const dust = new THREE.Points(dustGeo, dustMat);
            scene.add(dust);

            // 5. ANIMATION LOOP
            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                time += 0.01;
                controls.update();

                const sync = data.resonance.sync;
                // Fate Breath: Pulse magnitude depends on stability
                const breath = 1.0 + Math.sin(time * 1.5) * (0.05 + (1-sync)*0.1);
                
                shells.forEach(sh => {{
                    const pulse = 1.0 + Math.sin(time * 2 + sh.data.phase) * 0.05;
                    sh.mesh.scale.set(pulse * breath, pulse * breath, pulse * breath);
                    sh.mesh.rotation.y += 0.001;
                    if(data.resonance.mode === "BEATING") {{
                         sh.mesh.material.opacity = 0.05 + Math.sin(time * 5) * 0.05;
                    }} else {{
                         sh.mesh.material.opacity = 0.15;
                    }}
                }});

                pillarGroups.forEach(obj => {{
                    // Internal Binary Rotation
                    const orbitT = time * 2 + obj.timeOffset;
                    obj.stem.position.set(Math.cos(orbitT) * 1.2, 0, Math.sin(orbitT) * 1.2);
                    obj.branch.position.set(-Math.cos(orbitT) * 1.2, 0, -Math.sin(orbitT) * 1.2);
                    
                    // External Movement
                    if (obj.type === "NATAL") {{
                         obj.group.rotation.y += 0.005;
                         obj.group.position.y += Math.sin(time + obj.timeOffset) * 0.005;
                    }} else if (obj.type === "LUCK") {{
                         // Slow background field rotation
                         const angle = time * 0.1;
                         obj.group.position.set(Math.cos(angle)*25, -10, Math.sin(angle)*25);
                    }} else if (obj.type === "ANNUAL") {{
                         // Fast eccentric comet orbit
                         const angle = time * 1.2;
                         obj.group.position.set(Math.cos(angle)*35, 15 * Math.sin(angle*0.5), Math.sin(angle)*20);
                         obj.group.scale.set(1.5, 1.5, 1.5); // Highlight annual
                    }}
                }});

                dust.rotation.y += 0.0002;
                if(sync > 0.9) {{
                    dust.material.color.setHex(0xffffff); // Superconductive white
                }} else {{
                    dust.material.color.setHex(0x40e0d0);
                }}
                renderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=height)
