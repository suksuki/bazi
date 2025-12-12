
import streamlit as st
import streamlit.components.v1 as components
import json
import numpy as np
from core.wuxing_engine import WuXingEngine
from core.quantum import QuantumEngine

def render_3d_quantum_field(chart, strength_data, current_context=None, aspect_ratio=(1,1,0.8)):
    """
    Renders a Hyper-Realistic V4.0 Quantum Field using THREE.JS.
    Features: 
    - Full Shell-Core Particle Structure for ALL branches.
    - Cyclotron Loops for San He interactions.
    - Dynamic Shockwaves for Clashes.
    """

    st.subheader("🌌 三维量子场 (Quantum Field V4.0 Pro)")
    st.caption("🚀 视觉引擎: WebGL Standard. 启用全息壳核结构与相位锁定加速器。")
    
    # Physics Engine
    we = WuXingEngine(chart)
    qe = QuantumEngine({}, [], wuxing_engine=we)
    interactions = qe.calculate_interactions(chart)

    # 1. Prepare Data for Three.js
    nodes = []
    links = []
    effects = []
    
    # Topology: Spacetime Coordinates
    # Year/Month/Day/Hour spread on X-axis
    topo_pos = {
        'year':  {'x': -4.5, 'y': 0},
        'month': {'x': -1.5, 'y': 0},
        'day':   {'x': 1.5,  'y': 0},
        'hour':  {'x': 4.5,  'y': 0}
    }
    
    # Colors (Neon/Emissive Palette)
    wuxing_colors = {
        'Wood': {'hex': 0x00FF44, 'str': '#00FF44'}, 
        'Fire': {'hex': 0xFF3333, 'str': '#FF3333'}, 
        'Earth':{'hex': 0xD4AF37, 'str': '#D4AF37'}, # Gold
        'Metal':{'hex': 0xE0E0E0, 'str': '#E0E0E0'}, # Silver
        'Water':{'hex': 0x3388FF, 'str': '#3388FF'}
    }

    # Iterate Pillars
    for p_key in ['year', 'month', 'day', 'hour']:
        if p_key not in chart: continue
        
        bx = topo_pos[p_key]['x']
        by = topo_pos[p_key]['y']
        
        # --- A. STEM (The Wave Packet) ---
        stem = chart[p_key]['stem']
        s_elem = we.get_wuxing(stem)
        s_z = 3.0
        
        nodes.append({
            'type': 'stem',
            'id': f"{p_key}_stem",
            'char': stem,
            'pos': [bx, by, s_z],
            'color': wuxing_colors.get(s_elem, {'hex':0xFFFFFF})['hex'],
            'element': s_elem,
            'size': 0.6
        })
        
        # --- B. BRANCH (The Composite Particle) ---
        branch = chart[p_key]['branch']
        particle = we.get_particle_info(branch)
        shell = particle.get('shell', {})
        core_map = particle.get('core', {})
        
        b_z = -2.0
        
        # Build the detailed particle structure
        cores_data = []
        
        # Distribute cores spatially inside the shell
        import math
        idx = 0
        count = len(core_map)
        
        for h_stem, ratio in core_map.items():
            h_elem = we.get_wuxing(h_stem)
            
            # Position: Main Qi in center, others orbiting
            if ratio >= 0.5:
                # Main Core
                cx, cy, cz = 0, 0, 0
                c_size = 0.5 * ratio
                spin_speed = 0.05
            else:
                # Mantle/Residue (Orbiting)
                angle = (2 * math.pi / max(1, count-1)) * idx 
                radius = 0.5
                cx = radius * math.cos(angle)
                cy = radius * math.sin(angle)
                cz = (idx % 2 - 0.5) * 0.3 # Slight z-offset
                c_size = 0.4 * ratio
                spin_speed = 0.1
                idx += 1
                
            cores_data.append({
                'char': h_stem,
                'element': h_elem,
                'color': wuxing_colors.get(h_elem, {'hex':0x888888})['hex'],
                'ratio': ratio,
                'rel_pos': [cx, cy, cz],
                'size': max(0.15, c_size),
                'spin_speed': spin_speed
            })

        nodes.append({
            'type': 'branch',
            'id': f"{p_key}_branch",
            'char': branch,
            'pos': [bx, by, b_z],
            'shell_color': shell.get('color', '#888888'),
            'shell_spin': shell.get('spin', 1),
            'cores': cores_data,
            'size': 1.2 # Shell Radius
        })
        
        # Pillar Link
        links.append({'start': [bx, by, s_z], 'end': [bx, by, b_z], 'type': 'pillar'})

    # 2. Interactions (Cyclotrons & Beams)
    for event in interactions:
        etype = event['type']
        
        if etype == "PhaseLocking":
            # San He Cyclotron (Tri-Harmony)
            target_element = event['element']
            san_he_map = {
                "Water": ["申", "子", "辰"], "Fire": ["寅", "午", "戌"],
                "Wood": ["亥", "卯", "未"], "Metal": ["巳", "酉", "丑"]
            }
            required = san_he_map.get(target_element, [])
            
            loop_nodes = []
            for n in nodes:
                if n['type'] == 'branch' and n['char'] in required:
                    loop_nodes.append(n['pos'])
            
            # Create a loop if at least 2 points (e.g. half-harmony) or 3 for full
            if len(loop_nodes) >= 2: 
                effects.append({
                    'type': 'cyclotron',
                    'path': loop_nodes,
                    'color': wuxing_colors.get(target_element, {'hex':0xFFD700})['hex']
                })

        elif etype == "Resonance":
            # Beam
            s_node = next((n for n in nodes if n['id'] == event['source']), None)
            b_node = next((n for n in nodes if n['id'] == event['target']), None)
            if s_node and b_node:
                effects.append({
                    'type': 'beam',
                    'start': s_node['pos'],
                    'end': b_node['pos'],
                    'color': 0x00FFFF
                })

        elif etype == "ShellRupture":
            # Clash
            n1 = next((n for n in nodes if n['id'] == event['source']), None)
            n2 = next((n for n in nodes if n['id'] == event['target']), None)
            if n1 and n2:
                mid = [(a+b)/2 for a,b in zip(n1['pos'], n2['pos'])]
                effects.append({
                    'type': 'shockwave',
                    'pos': mid,
                    'color': 0xFF0000
                })

    viz_payload = {'nodes': nodes, 'links': links, 'effects': effects}
    html = generate_high_fidelity_html(viz_payload)
    components.html(html, height=700, scrolling=False)


def generate_high_fidelity_html(data):
    json_str = json.dumps(data)
    
    # IMPORTANT: We use {{ }} to escape braces in Python f-string
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <style>body {{ margin: 0; overflow: hidden; background: #000; }}</style>
        <script type="importmap">
          {{ "imports": {{ 
              "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
              "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
          }} }}
        </script>
    </head>
    <body>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

        // NOTE: Bloom disabled for stability
        // import {{ UnrealBloomPass }} from 'three/addons/postprocessing/UnrealBloomPass.js';
        // import {{ EffectComposer }} from 'three/addons/postprocessing/EffectComposer.js';
        // import {{ RenderPass }} from 'three/addons/postprocessing/RenderPass.js';

        const data = {json_str};

        // --- SCENE ---
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000205, 0.02); 

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, -18, 12); 
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        // renderer.toneMapping = THREE.ACESFilmicToneMapping;
        document.body.appendChild(renderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // --- LIGHTS ---
        scene.add(new THREE.AmbientLight(0xffffff, 2.0));
        const pl = new THREE.PointLight(0xffffff, 2.0, 50);
        pl.position.set(5, 5, 5);
        scene.add(pl);
        
        // --- GRID ---
        const grid = new THREE.GridHelper(50, 50, 0x445566, 0x111111);
        grid.rotation.x = Math.PI / 2;
        grid.position.z = -5; 
        scene.add(grid);

        // --- HELPERS ---
        function createTextSprite(char, colorStr, scale=1.0) {{
            const canvas = document.createElement('canvas');
            canvas.width = 256; canvas.height = 256;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = colorStr;
            ctx.font = 'bold 150px "Microsoft YaHei", sans-serif'; 
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(char, 128, 128);
            
            const tex = new THREE.CanvasTexture(canvas);
            const mat = new THREE.SpriteMaterial({{ map: tex, transparent: true }});
            const sprite = new THREE.Sprite(mat);
            sprite.scale.set(scale, scale, 1);
            return sprite;
        }}

        const rotators = [];

        // --- RENDER NODES ---
        data.nodes.forEach(node => {{
            const grp = new THREE.Group();
            grp.position.set(...node.pos);
            
            if (node.type === 'stem') {{
                const geo = new THREE.IcosahedronGeometry(node.size, 2);
                const mat = new THREE.MeshStandardMaterial({{
                    color: node.color, emissive: node.color, emissiveIntensity: 0.5,
                    roughness: 0.2, metalness: 0.1
                }});
                grp.add(new THREE.Mesh(geo, mat));
                
                const txt = createTextSprite(node.char, '#ffffff', 2.0);
                txt.position.y += 1.0;
                grp.add(txt);
                
                grp.userData = {{ spin: 0.01, axis: 'z' }};
                rotators.push(grp);
                
            }} else if (node.type === 'branch') {{
                // === SHELL ===
                const shellGeo = new THREE.SphereGeometry(node.size, 32, 32);
                const shellMat = new THREE.MeshPhysicalMaterial({{
                    color: node.shell_color, 
                    metalness: 0.0, roughness: 0.1, transmission: 0.9, opacity: 0.6, transparent: true,
                    side: THREE.FrontSide
                }});
                const shell = new THREE.Mesh(shellGeo, shellMat);
                grp.add(shell);
                
                // === RING ===
                const ringGeo = new THREE.TorusGeometry(node.size * 1.4, 0.03, 16, 32);
                const ringMat = new THREE.MeshBasicMaterial({{ color: node.shell_color, transparent: true, opacity: 0.8 }});
                const ring = new THREE.Mesh(ringGeo, ringMat);
                if (node.shell_spin === 1) ring.rotation.x = Math.PI / 2;
                else ring.rotation.y = Math.PI / 2;
                grp.add(ring);
                ring.userData = {{ spin: 0.02 * node.shell_spin, axis: (node.shell_spin === 1 ? 'z' : 'x') }};
                rotators.push(ring);

                // === CORES ===
                if (node.cores) {{
                    node.cores.forEach(core => {{
                        const cGrp = new THREE.Group();
                        cGrp.position.set(...core.rel_pos);
                        
                        const cGeo = new THREE.SphereGeometry(core.size, 16, 16);
                        const cMat = new THREE.MeshStandardMaterial({{
                            color: core.color, emissive: core.color, emissiveIntensity: 0.5
                        }});
                        cGrp.add(new THREE.Mesh(cGeo, cMat));
                        
                        // Label
                        const cTxt = createTextSprite(core.char, '#fff', core.size * 3.5);
                        cTxt.position.z += core.size + 0.1;
                        cGrp.add(cTxt);
                        
                        grp.add(cGrp);
                    }});
                }}
                
                // Main Branch Label
                const bTxt = createTextSprite(node.char, node.shell_color, 2.8);
                bTxt.position.y -= node.size + 1.2;
                grp.add(bTxt);
            }}
            scene.add(grp);
        }});

        // --- RENDER EFFECTS ---
        data.effects.forEach(eff => {{
            if (eff.type === 'cyclotron') {{
                const pts = eff.path.map(p => new THREE.Vector3(...p));
                if (pts.length > 2) pts.push(pts[0]);
                
                const curve = new THREE.CatmullRomCurve3(pts);
                const geo = new THREE.TubeGeometry(curve, 64, 0.15, 8, false);
                const mat = new THREE.MeshBasicMaterial({{ color: eff.color, transparent: true, opacity: 0.6 }});
                const tube = new THREE.Mesh(geo, mat);
                scene.add(tube);
                
                tube.userData = {{ pulse: true }};
                rotators.push(tube);

            }} else if (eff.type === 'beam') {{
                const s = new THREE.Vector3(...eff.start);
                const e = new THREE.Vector3(...eff.end);
                
                const geo = new THREE.BufferGeometry().setFromPoints([s, e]);
                const mat = new THREE.LineBasicMaterial({{ color: eff.color }});
                scene.add(new THREE.Line(geo, mat));
                
            }} else if (eff.type === 'shockwave') {{
                const geo = new THREE.RingGeometry(0.1, 1.5, 32);
                const mat = new THREE.MeshBasicMaterial({{ color: eff.color, side: THREE.DoubleSide, transparent: true, opacity: 0.8 }});
                const mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(...eff.pos);
                scene.add(mesh);
                mesh.userData = {{ expand: true, scale: 0.1 }};
                rotators.push(mesh);
            }}
        }});
        
        // --- ANIMATION ---
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            
            rotators.forEach(o => {{
                if (o.userData.spin) {{
                    o.rotation[o.userData.axis || 'y'] += o.userData.spin;
                }}
                if (o.userData.pulse) {{
                    const t = Date.now() * 0.002;
                    o.material.opacity = 0.4 + Math.sin(t)*0.2;
                }}
                if (o.userData.expand) {{
                    o.userData.scale += 0.05;
                    o.scale.setScalar(o.userData.scale);
                    o.material.opacity = 1.0 - (o.userData.scale / 4.0);
                    if (o.material.opacity <= 0) {{ 
                        o.userData.scale = 0.1; o.material.opacity = 1.0; 
                    }}
                }}
            }});
            
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
