import streamlit.components.v1 as components
import json

def render_molviz_3d(nodes, edges, height=500):
    """
    Renders a 3D Molecule visualization using Three.js.
    
    Args:
        nodes: List of dicts {'id': 'Year', 'label': 'Year', 'color': '#ff0000'}
        edges: List of dicts {'source': 'Year', 'target': 'Month', 'color': 'green', 'type': 'dashed'}
    """
    
    # 1. Prepare Data for JS
    data_json = json.dumps({'nodes': nodes, 'edges': edges})
    
    # 2. HTML Template with Three.js
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Quantum MolViz</title>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #0e1117; color: #ff4b4b; font-family: monospace; }}
            canvas {{ width: 100%; height: 100%; display: block; }}
            #status {{ position: absolute; top: 10px; left: 10px; z-index: 100; pointer-events: none; }}
        </style>
        <!-- Load Three.js from CDN -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="status">Initializing 3D Engine...</div>
        <div id="container"></div>
        <script>
            window.onerror = function(message, source, lineno, colno, error) {{
                document.getElementById('status').innerText = "Error: " + message + " at line " + lineno;
                return false;
            }};

            try {{
                if (typeof THREE === 'undefined') {{
                    throw new Error("Three.js not loaded. Check Internet Connection.");
                }}
                
                document.getElementById('status').innerText = ""; // Clear Loading
                
                const data = {data_json};
                
                // 1. Scene Setup
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0e1117); 
                
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(0, 2, 5);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.getElementById('container').appendChild(renderer.domElement);
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040); 
                scene.add(ambientLight);
                const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
                directionalLight.position.set(5, 10, 7);
                scene.add(directionalLight);
                
                // Controls
                // Check if OrbitControls is attached to THREE
                let ControlsClass = THREE.OrbitControls;
                if (!ControlsClass && window.OrbitControls) ControlsClass = window.OrbitControls;
                if (!ControlsClass) console.warn("OrbitControls not found, navigation disabled.");
                
                const controls = ControlsClass ? new ControlsClass(camera, renderer.domElement) : null;
                if (controls) {{
                    controls.enableDamping = true;
                    controls.autoRotate = true;
                    controls.autoRotateSpeed = 1.0;
                }}
                
                // 2. Geometry
                const positions = {{
                    'Year':  new THREE.Vector3(0, 1.5, 0),
                    'Month': new THREE.Vector3(-1.2, -0.5, 1.2),
                    'Day':   new THREE.Vector3(1.2, -0.5, 1.2),
                    'Hour':  new THREE.Vector3(0, -0.5, -1.5)
                }};
                
                let nodePos = {{}};
                data.nodes.forEach((n, idx) => {{
                    let label = n.label.split("\\n")[0]; 
                    if (positions[label]) {{
                        nodePos[n.id] = positions[label];
                    }} else {{
                        // Default layout
                        let angle = (idx / data.nodes.length) * Math.PI * 2;
                        nodePos[n.id] = new THREE.Vector3(Math.cos(angle)*2, 0, Math.sin(angle)*2);
                    }}
                    
                    // Standard Glass Material (Physical)
                    const geometry = new THREE.SphereGeometry(0.6, 64, 32); // Smoother
                    // MeshPhysicalMaterial for better glass effect
                    const material = new THREE.MeshPhysicalMaterial({{ 
                        color: n.color, 
                        metalness: 0.1,
                        roughness: 0.1,
                        transmission: 0.6, // Glass-like transparency
                        thickness: 1.0, 
                        transparent: true,
                        opacity: 0.5,
                        side: THREE.DoubleSide,
                        depthWrite: false, 
                    }});
                    
                    const sphere = new THREE.Mesh(geometry, material);
                    sphere.position.copy(nodePos[n.id]);
                    scene.add(sphere);
                    
                    // Inner Nucleus (Glowing Core)
                    const coreGeo = new THREE.SphereGeometry(0.2, 32, 16);
                    const coreMat = new THREE.MeshBasicMaterial({{ color: n.color }}); // Emanating light
                    const core = new THREE.Mesh(coreGeo, coreMat);
                    core.position.copy(nodePos[n.id]);
                    scene.add(core);

                    // Text Label
                    const textParts = n.label.split("|");
                    const mainText = textParts.length > 1 ? textParts[1] : textParts[0];
                    const subText = textParts[0];

                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.width = 512; canvas.height = 512;
                    
                    // Draw Main Char (Full Pillar e.g. "甲子")
                    // Reduced Size: 110px (was 160px)
                    context.font = 'Bold 110px "Microsoft YaHei", sans-serif'; 
                    context.fillStyle = "rgba(255,255,255,1)";
                    context.textAlign = "center";
                    context.textBaseline = "middle";
                    context.shadowColor = "rgba(0,0,0,0.8)";
                    context.shadowBlur = 8;
                    context.fillText(mainText, 256, 240);
                    
                    // Draw Sub Label (Axis e.g. "年柱")
                    // Reduced Size: 40px
                    context.font = 'Bold 40px "Microsoft YaHei", sans-serif'; // Chinese font support
                    context.fillStyle = "rgba(220,220,220,0.9)";
                    context.fillText(subText, 256, 340);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const spriteMat = new THREE.SpriteMaterial({{ map: texture, depthTest: false }});
                    
                    const sprite = new THREE.Sprite(spriteMat);
                    sprite.position.copy(nodePos[n.id]);
                    sprite.scale.set(1.4, 1.4, 1.4); 
                    scene.add(sprite);
                }});
                
                // Texture Generator for Energy Flow
                function createFlowTexture(colorStr) {{
                    const canvas = document.createElement('canvas');
                    canvas.width = 64; canvas.height = 64;
                    const ctx = canvas.getContext('2d');
                    
                    // Transparent background
                    ctx.fillStyle = 'rgba(0,0,0,0)';
                    ctx.fillRect(0,0,64,64);
                    
                    // Dashed Gradient Line (Energy Pulse)
                    const gradient = ctx.createLinearGradient(0, 0, 0, 64);
                    gradient.addColorStop(0, 'rgba(0,0,0,0)');
                    gradient.addColorStop(0.5, colorStr); 
                    gradient.addColorStop(1, 'rgba(0,0,0,0)');
                    
                    ctx.fillStyle = gradient;
                    ctx.fillRect(20, 0, 24, 64); // Center strip
                    
                    const tex = new THREE.CanvasTexture(canvas);
                    tex.wrapS = THREE.RepeatWrapping;
                    tex.wrapT = THREE.RepeatWrapping;
                    // Rotate texture to align with cylinder Y?
                    // Cylinder maps U around, V along height. 
                    // We drew gradient along Y (0->64). So it should match V.
                    // We will animate offset.y
                    tex.repeat.set(1, 4); // Repeat 4 times along length
                    return tex;
                }}

                // Store animatable textures
                const flowTextures = [];

                // Edges
                data.edges.forEach(e => {{
                    const start = nodePos[e.source];
                    const end = nodePos[e.target];
                    
                    if (start && end) {{
                        const distance = start.distanceTo(end);
                        const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
                        
                        // 1. Thinner Tube (Energy Beam)
                        const geometry = new THREE.CylinderGeometry(0.02, 0.02, distance, 8);
                        
                        // Animated Texture Material
                        // We need a unique texture per color or clone it? 
                        // CanvasTexture is cheap enough to make per edge for ease, or cache by color.
                        // Let's cache? Nah, simple first.
                        const flowTex = createFlowTexture(e.color);
                        flowTextures.push(flowTex);
                        
                        const material = new THREE.MeshBasicMaterial({{ 
                            map: flowTex,
                            transparent: true,
                            opacity: 0.8,
                            side: THREE.DoubleSide,
                            blending: THREE.AdditiveBlending, // Glow effect
                            depthWrite: false
                        }});
                        
                        const cylinder = new THREE.Mesh(geometry, material);
                        cylinder.position.copy(mid);
                        cylinder.lookAt(end);
                        cylinder.rotateX(Math.PI / 2); // Align Y axis to LookAt vector
                        scene.add(cylinder);
                        
                        // 2. Arrowhead (Direction Indicator)
                        // Place at 2/3 distance towards target
                        const dir = new THREE.Vector3().subVectors(end, start).normalize();
                        const arrowPos = new THREE.Vector3().copy(start).add(dir.multiplyScalar(distance * 0.66));
                        
                        const coneGeo = new THREE.ConeGeometry(0.08, 0.2, 16);
                        const coneMat = new THREE.MeshBasicMaterial({{ color: e.color }});
                        const cone = new THREE.Mesh(coneGeo, coneMat);
                        cone.position.copy(arrowPos);
                        cone.lookAt(end);
                        cone.rotateX(Math.PI / 2); 
                        scene.add(cone);
                    }}
                }});
                
                // 3. Loop
                function animate() {{
                    requestAnimationFrame(animate);
                    if (controls) controls.update();
                    
                    // Animate Flow Textures
                    flowTextures.forEach(tex => {{
                        tex.offset.y -= 0.02; // Flow towards target
                    }});
                    
                    renderer.render(scene, camera);
                }}
                animate();
                
                window.addEventListener('resize', () => {{
                   camera.aspect = window.innerWidth / window.innerHeight;
                   camera.updateProjectionMatrix();
                   renderer.setSize(window.innerWidth, window.innerHeight);
                }}, false);

            }} catch (err) {{
                document.getElementById('status').innerText = "Runtime Error: " + err.message;
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=height)
