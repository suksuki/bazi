import streamlit.components.v1 as components
import json

def render_molviz_3d(nodes, edges, height=500):
    """
    Renders a 3D Interaction Network using Hollow Wireframe Spheres (Cages).
    Each node (Pillar) is a Binary system of two cages.
    Inside the cages are small Chinese character labels representing the Stem and Branch.
    """
    
    # Pre-process nodes to separate Stem/Branch if label contains '|'
    # Format: label: 'Year|甲子'
    processed_nodes = []
    for n in nodes:
        label = n.get('label', '|')
        parts = label.split('|')
        axis = parts[0] if len(parts) > 0 else "Unknown"
        char_pair = parts[1] if len(parts) > 1 else "??"
        
        processed_nodes.append({
            "id": n['id'],
            "axis": axis,
            "stem_char": char_pair[0] if len(char_pair) > 0 else "?",
            "branch_char": char_pair[1] if len(char_pair) > 1 else "?",
            "color": n.get('color', '#ffffff')
        })

    data_json = json.dumps({'nodes': processed_nodes, 'edges': edges})
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #050710; }}
            #container {{ width: 100%; height: {height}px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="container"></div>
        <script>
            const data = {data_json};
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('container').appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            camera.position.set(0, 5, 12);
            controls.enableDamping = true;

            scene.add(new THREE.AmbientLight(0xffffff, 0.3));
            
            // Placement for the 4 pillars
            const positions = {{
                '年柱': new THREE.Vector3(-4, 2, -2),
                '月柱': new THREE.Vector3(-1.5, 0, 2),
                '日柱': new THREE.Vector3(1.5, 0, 2),
                '时柱': new THREE.Vector3(4, -2, -2)
            }};

            const nodeObjects = {{}};

            // Helper to generate text texture
            function createTextTexture(text, color) {{
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 128; canvas.height = 128;
                ctx.font = 'Bold 80px "Microsoft YaHei", "Heiti SC", sans-serif';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.shadowColor = 'rgba(0,0,0,0.5)';
                ctx.shadowBlur = 4;
                ctx.fillText(text, 64, 64);
                return new THREE.CanvasTexture(canvas);
            }}

            data.nodes.forEach((n, idx) => {{
                const group = new THREE.Group();
                const pos = positions[n.axis] || new THREE.Vector3(Math.cos(idx)*5, Math.sin(idx)*5, 0);
                group.position.copy(pos);
                
                // --- Hollow Cage System ---
                
                // P1: Stem Cage (Wireframe)
                const p1Geo = new THREE.SphereGeometry(0.35, 16, 16);
                const p1Mat = new THREE.MeshBasicMaterial({{ color: n.color, wireframe: true, transparent: true, opacity: 0.4 }});
                const p1 = new THREE.Mesh(p1Geo, p1Mat);
                group.add(p1);

                // Stem Text (Inside Cage)
                const sTex = createTextTexture(n.stem_char, n.color);
                const sSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: sTex, depthTest: false }}));
                sSprite.scale.set(0.5, 0.5, 0.5);
                p1.add(sSprite);

                // P2: Branch Cage (Wireframe)
                const p2Geo = new THREE.SphereGeometry(0.45, 16, 16);
                const p2Mat = new THREE.MeshBasicMaterial({{ color: n.color, wireframe: true, transparent: true, opacity: 0.4 }});
                const p2 = new THREE.Mesh(p2Geo, p2Mat);
                group.add(p2);

                // Branch Text (Inside Cage)
                const bTex = createTextTexture(n.branch_char, n.color);
                const bSprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: bTex, depthTest: false }}));
                bSprite.scale.set(0.6, 0.6, 0.6);
                p2.add(bSprite);

                // Connection line
                const beamGeo = new THREE.CylinderGeometry(0.01, 0.01, 0.8, 8);
                const beamMat = new THREE.MeshBasicMaterial({{ color: '#ffffff', transparent: true, opacity: 0.2 }});
                const beam = new THREE.Mesh(beamGeo, beamMat);
                beam.rotation.z = Math.PI/2;
                group.add(beam);

                scene.add(group);
                nodeObjects[n.id] = {{ group, p1, p2, basePos: pos.clone() }};
            }});

            // 2. Edges (Interactions - Keep the arc logic)
            data.edges.forEach(e => {{
                const startNode = nodeObjects[e.source];
                const endNode = nodeObjects[e.target];
                if (startNode && endNode) {{
                    const curve = new THREE.QuadraticBezierCurve3(
                        startNode.basePos,
                        new THREE.Vector3((startNode.basePos.x + endNode.basePos.x)/2, 2, (startNode.basePos.z + endNode.basePos.z)/2),
                        endNode.basePos
                    );
                    const edgeGeo = new THREE.TubeGeometry(curve, 20, 0.02, 8, false);
                    const edgeMat = new THREE.MeshBasicMaterial({{ color: e.color || '#ffffff', transparent: true, opacity: 0.3 }});
                    scene.add(new THREE.Mesh(edgeGeo, edgeMat));
                    
                    const pGeo = new THREE.SphereGeometry(0.06, 8, 8);
                    const flowP = new THREE.Mesh(pGeo, new THREE.MeshBasicMaterial({{ color: e.color || '#ffffff' }}));
                    scene.add(flowP);
                    endNode.flows = endNode.flows || [];
                    endNode.flows.push({{ mesh: flowP, curve, t: Math.random() }});
                }}
            }});

            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                time += 0.02;
                controls.update();

                Object.values(nodeObjects).forEach((obj, idx) => {{
                    const orbitT = time * 4 + idx;
                    const d = 0.5;
                    obj.p1.position.set(Math.cos(orbitT)*d, Math.sin(orbitT)*d, 0);
                    obj.p2.position.set(-Math.cos(orbitT)*d, -Math.sin(orbitT)*d, 0);
                    obj.group.position.y = obj.basePos.y + Math.sin(time + idx)*0.15;
                    if (obj.flows) {{
                        obj.flows.forEach(f => {{
                            f.t += 0.005; if (f.t > 1) f.t = 0;
                            const p = f.curve.getPoint(f.t);
                            f.mesh.position.copy(p);
                        }});
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
    
    components.html(html_code, height=height)
