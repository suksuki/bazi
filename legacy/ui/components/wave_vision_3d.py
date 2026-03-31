
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
    
    # 1. Prepare Chrono-Data (Binary Stars & Hidden Stems)
    from core.trinity.core.nexus.definitions import BaziParticleNexus
    pillars_data = []
    
    # Elemental Color Map
    elem_colors = {
        "Wood": "#4ade80", "Fire": "#f87171", "Earth": "#fdba74", "Metal": "#94a3b8", "Water": "#38bdf8"
    }

    # Stem Atomic Mapping for Sigils
    stem_codes = {
        "甲": ("WD+", "#4ade80"), "乙": ("WD-", "#4ade80"),
        "丙": ("FR+", "#f87171"), "丁": ("FR-", "#f87171"),
        "戊": ("ER+", "#fdba74"), "己": ("ER-", "#fdba74"),
        "庚": ("MT+", "#94a3b8"), "辛": ("MT-", "#94a3b8"),
        "壬": ("WT+", "#38bdf8"), "癸": ("WT-", "#38bdf8")
    }
    
    # Branch Element Mapping for Sigils
    branch_map = {
        "子": "WT", "亥": "WT", "寅": "WD", "卯": "WD",
        "巳": "FR", "午": "FR", "申": "MT", "酉": "MT",
        "辰": "ER", "戌": "ER", "丑": "ER", "未": "ER"
    }

    bazi_list = full_bazi_context if full_bazi_context else []
    for i in range(min(6, len(bazi_list))):
        p_str = bazi_list[i]
        if not p_str or len(p_str) < 2: 
            continue
            
        p_type = "NATAL"
        if i == 4: p_type = "LUCK"
        if i == 5: p_type = "ANNUAL"
        
        s_char, b_char = p_str[0], p_str[1]
        
        # Get Stem Meta with safe defaults
        s_code, s_color = stem_codes.get(s_char, ("ER+", "#ffffff"))
        
        # Get Branch Meta & Hidden Stems
        b_elem_code = branch_map.get(b_char, "ER")
        b_meta = BaziParticleNexus.BRANCHES.get(b_char, ("Earth", 0, []))
        b_color = elem_colors.get(b_meta[0], "#ffffff")
        
        hidden = []
        for h_char, _ in b_meta[2]:
            _, h_color = stem_codes.get(h_char, ("ER+", "#ffffff"))
            hidden.append({"color": h_color})
            
        pillars_data.append({
            "type": p_type,
            "stem": {"code": s_code, "color": s_color},
            "branch": {"code": f"B-{b_elem_code}", "color": b_color, "hidden": hidden},
            "id": i
        })
    
    # 2. Prepare Element Shells
    elements_data = []
    for name, color in elem_colors.items():
        wave = waves.get(name, WaveState(amplitude=0, phase=0)) if waves else WaveState(0,0)
        elements_data.append({
            "name": name, "color": color, 
            "amplitude": float(wave.amplitude), 
            "phase": float(wave.phase)
        })

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
                position: absolute; bottom: 30px; right: 30px;
                color: #ff9f43; font-family: 'Courier New', Courier, monospace;
                pointer-events: none; text-align: right;
                border-right: 2px solid #ff9f43; padding-right: 15px;
                background: rgba(0,0,0,0.5); padding: 10px;
                border-radius: 4px;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="hud">
            [QUANTUM ORRERY V5.3]<br>
            STATUS: ACTIVE<br>
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
            camera.position.set(15, 10, 15);
            controls.enableDamping = true;

            // 1. LIGHTING
            scene.add(new THREE.AmbientLight(0xffffff, 0.3));
            const pLight = new THREE.PointLight(0xffffff, 1.5, 60);
            pLight.position.set(0, 15, 0);
            scene.add(pLight);

            // 2. SHELLS
            const shells = [];
            data.elements.forEach((el, idx) => {{
                if(el.amplitude < 0.05) return;
                const radius = 6 + idx * 1.8;
                const geom = new THREE.SphereGeometry(radius, 48, 36);
                const mat = new THREE.MeshBasicMaterial({{
                    color: el.color, wireframe: true, transparent: true, opacity: 0.1
                }});
                const shell = new THREE.Mesh(geom, mat);
                scene.add(shell);
                shells.push({{ mesh: shell, baseRadius: radius, data: el }});
            }});

            function createSigilTexture(type, color, polarity = "Yang") {{
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 512; canvas.height = 512;
                
                ctx.clearRect(0, 0, 512, 512);
                ctx.strokeStyle = color;
                ctx.lineWidth = 20;
                ctx.shadowColor = color;
                ctx.shadowBlur = 40;
                const center = 256;

                ctx.beginPath();
                if (type === "WD") {{
                    ctx.moveTo(center-60, center+120); ctx.lineTo(center-60, center-120);
                    ctx.moveTo(center, center+150); ctx.lineTo(center, center-150);
                    ctx.moveTo(center+60, center+120); ctx.lineTo(center+60, center-120);
                }} else if (type === "FR") {{
                    ctx.moveTo(center, center-160); ctx.lineTo(center-140, center+100); ctx.lineTo(center+140, center+100); ctx.closePath();
                }} else if (type === "ER") {{
                    ctx.rect(center-120, center-120, 240, 240);
                }} else if (type === "MT") {{
                    ctx.arc(center, center, 140, 0, Math.PI*2); ctx.stroke(); ctx.beginPath(); ctx.arc(center, center, 80, 0, Math.PI*2);
                }} else if (type === "WT") {{
                    for(let i=-1; i<=1; i++) {{
                        ctx.moveTo(center-180, center + i*80);
                        for(let x=-180; x<=180; x+=10) {{ ctx.lineTo(center+x, center + i*80 + Math.sin(x*0.05)*30); }}
                    }}
                }}
                ctx.stroke();
                
                ctx.beginPath();
                ctx.setLineDash(polarity === "Yang" ? [] : [30, 20]);
                ctx.lineWidth = 10;
                ctx.arc(center, center, 240, 0, Math.PI*2);
                ctx.stroke();
                return new THREE.CanvasTexture(canvas);
            }}

            const starGeo = new THREE.SphereGeometry(0.5, 32, 32);
            const branchGeo = new THREE.SphereGeometry(1.6, 32, 32);
            const pillarGroups = [];

            data.pillars.forEach((p, idx) => {{
                const group = new THREE.Group();
                const orbitR = (p.type === "NATAL") ? 8 : (p.type === "LUCK" ? 22 : 27);
                
                if (p.type === "NATAL") {{
                    const angle = (idx / 4) * Math.PI * 2;
                    group.position.set(Math.cos(angle)*8, (Math.random()-0.5)*2, Math.sin(angle)*8);
                }}
                scene.add(group);
                
                const sMat = new THREE.MeshPhongMaterial({{ color: p.stem.color, emissive: p.stem.color, emissiveIntensity: 3 }});
                const stemStar = new THREE.Mesh(starGeo, sMat);
                group.add(stemStar);
                
                const sType = p.stem.code ? p.stem.code.substring(0,2) : "ER";
                const sPol = p.stem.code && p.stem.code.endsWith("+") ? "Yang" : "Yin";
                const sTex = createSigilTexture(sType, p.stem.color, sPol);
                const sSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: sTex, transparent: true }}));
                sSprite.scale.set(3.2, 3.2, 3.2);
                stemStar.add(sSprite);

                const bMat = new THREE.MeshBasicMaterial({{ color: p.branch.color, wireframe: true, transparent: true, opacity: 0.25 }});
                const branchSphere = new THREE.Mesh(branchGeo, bMat);
                group.add(branchSphere);
                
                const bType = p.branch.code ? p.branch.code.split("-")[1] : "ER";
                const bTex = createSigilTexture(bType, p.branch.color, "Yang");
                const bSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: bTex, transparent: true }}));
                bSprite.scale.set(4.8, 4.8, 4.8);
                branchSphere.add(bSprite);

                // --- Quantum Spark Arcs (High-energy EM interaction) ---
                const fluxLines = [];
                for(let k=0; k<5; k++) {{
                    const lineGeo = new THREE.BufferGeometry();
                    const lineMat = new THREE.LineBasicMaterial({{ 
                        color: p.stem.color, 
                        transparent: true, 
                        opacity: 0.6,
                        blending: THREE.AdditiveBlending
                    }});
                    const line = new THREE.Line(lineGeo, lineMat);
                    group.add(line);
                    fluxLines.push(line);
                }}

                const hiddenStars = [];
                (p.branch.hidden || []).forEach((h, hIdx) => {{
                    const hMat = new THREE.MeshPhongMaterial({{ color: h.color, emissive: h.color, emissiveIntensity: 4 }});
                    const hStar = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 12), hMat);
                    const hAngle = (hIdx / p.branch.hidden.length) * Math.PI * 2;
                    hStar.position.set(Math.cos(hAngle)*1.0, Math.sin(hAngle)*1.0, 0);
                    branchSphere.add(hStar);
                    hiddenStars.push(hStar);
                }});

                pillarGroups.push({{ 
                    group, stem: stemStar, branch: branchSphere, flux: fluxLines,
                    hidden: hiddenStars, timeOffset: idx * 2.3, type: p.type, polarity: sPol,
                    sSprite, bSprite, color: p.stem.color
                }});
            }});

            const dustGeo = new THREE.BufferGeometry();
            const dustPos = [];
            for (let i = 0; i < 3500; i++) {{
                dustPos.push((Math.random()-0.5)*120, (Math.random()-0.5)*120, (Math.random()-0.5)*120);
            }}
            dustGeo.setAttribute('position', new THREE.Float32BufferAttribute(dustPos, 3));
            const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({{ color: 0x40e0d0, size: 0.12, transparent: true, opacity: 0.4 }}));
            scene.add(dust);

            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                time += 0.01;
                controls.update();
                const sync = data.resonance.sync;
                const breath = 1.0 + Math.sin(time * 1.5) * (0.05 + (1-sync)*0.1);
                
                shells.forEach(sh => {{
                    const pulse = 1.0 + Math.sin(time * 2 + sh.data.phase) * 0.05;
                    sh.mesh.scale.set(pulse * breath, pulse * breath, pulse * breath);
                    sh.mesh.rotation.y += 0.001;
                }});

                pillarGroups.forEach(obj => {{
                    const orbitT = time * 1.2 + obj.timeOffset;
                    const r = 2.6;
                    
                    const sPos = new THREE.Vector3(Math.cos(orbitT) * r, Math.sin(orbitT * 0.4) * 0.8, Math.sin(orbitT) * r);
                    const bPos = new THREE.Vector3(-Math.cos(orbitT) * r, -Math.sin(orbitT * 0.4) * 0.8, -Math.sin(orbitT) * r);
                    
                    obj.stem.position.copy(sPos);
                    obj.branch.position.copy(bPos);
                    
                    const rotDir = (obj.polarity === "Yang") ? 1 : -1;
                    obj.sSprite.material.rotation += 0.02 * rotDir;
                    obj.bSprite.material.rotation -= 0.01;

                    // Update Spark Arcs (Jittery & High Energy)
                    obj.flux.forEach((line, k) => {{
                        const jitter = (Math.random() - 0.5) * 2;
                        const controlPoint = new THREE.Vector3(
                            (sPos.x + bPos.x)/2 + (Math.sin(time * 10 + k) * 2) + jitter,
                            (sPos.y + bPos.y)/2 + (Math.cos(time * 8 + k) * 2) + jitter,
                            (sPos.z + bPos.z)/2 + (Math.sin(time * 12 + k) * 2) + jitter
                        );
                        const curve = new THREE.QuadraticBezierCurve3(sPos, controlPoint, bPos);
                        const points = curve.getPoints(12);
                        line.geometry.setFromPoints(points);
                        line.material.opacity = (Math.random() > 0.3) ? (0.3 + Math.random() * 0.7) : 0.1;
                        if(Math.random() > 0.95) line.material.color.setHex(0xffffff); // Flash white
                        else line.material.color.setStyle(obj.color);
                    }});

                    obj.branch.rotation.y += 0.015;
                    obj.hidden.forEach((h, hi) => {{ h.position.y = Math.sin(time * 2 + hi) * 0.3; }});

                    if (obj.type === "LUCK") {{
                         const angle = time * 0.12;
                         obj.group.position.set(Math.cos(angle)*32, -12, Math.sin(angle)*32);
                    }} else if (obj.type === "ANNUAL") {{
                         const angle = time * 0.8;
                         obj.group.position.set(Math.cos(angle)*42, 22 * Math.sin(angle*0.35), Math.sin(angle)*27);
                    }}
                }});
                dust.rotation.y += 0.0003;
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
