import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import {
  relationRefsForFrame,
  type MingliSceneFrame,
} from "../mingliSceneDirector";
import type {
  MingliStageBody,
  MingliStageColumn,
  MingliStageProjection,
  MingliStageRelation,
} from "../mingliStageTypes";

const ELEMENT_COLORS: Record<string, string> = {
  甲: "#7fcf9b",
  乙: "#7fcf9b",
  寅: "#7fcf9b",
  卯: "#7fcf9b",
  丙: "#ef8c68",
  丁: "#ef8c68",
  巳: "#ef8c68",
  午: "#ef8c68",
  戊: "#d4b074",
  己: "#d4b074",
  辰: "#d4b074",
  戌: "#d4b074",
  丑: "#d4b074",
  未: "#d4b074",
  庚: "#d5d8d1",
  辛: "#d5d8d1",
  申: "#d5d8d1",
  酉: "#d5d8d1",
  壬: "#78b9d0",
  癸: "#78b9d0",
  子: "#78b9d0",
  亥: "#78b9d0",
};

const DAYLIGHT_ELEMENT_COLORS: Record<string, string> = {
  甲: "#2f724e",
  乙: "#2f724e",
  寅: "#2f724e",
  卯: "#2f724e",
  丙: "#a04430",
  丁: "#a04430",
  巳: "#a04430",
  午: "#a04430",
  戊: "#846123",
  己: "#846123",
  辰: "#846123",
  戌: "#846123",
  丑: "#846123",
  未: "#846123",
  庚: "#53635c",
  辛: "#53635c",
  申: "#53635c",
  酉: "#53635c",
  壬: "#286b83",
  癸: "#286b83",
  子: "#286b83",
  亥: "#286b83",
};

interface BodyPlacement {
  body: MingliStageBody;
  column: MingliStageColumn;
  position: [number, number, number];
}

export default function MingliSceneCanvas({
  daylight,
  frame,
  onContextLost,
  stage,
}: {
  daylight: boolean;
  frame: MingliSceneFrame;
  onContextLost: () => void;
  stage: MingliStageProjection;
}) {
  const placements = useMemo(() => placeBodies(stage), [stage]);
  const positionsByColumn = useMemo(
    () =>
      new Map(
        stage.columns.map((column, index) => [
          column.column_ref,
          columnX(index, stage.columns.length),
        ]),
      ),
    [stage.columns],
  );
  const activeRelationRefs = relationRefsForFrame(stage, frame);
  const relationMemberColumnRefs = useMemo(
    () => relationColumnRefs(stage, activeRelationRefs),
    [activeRelationRefs, stage],
  );
  const narratedColumnRefs = useMemo(
    () => new Set(frame.activeColumnRefs),
    [frame.activeColumnRefs],
  );

  return (
    <Canvas
      camera={{ fov: 38, position: [0, 0.15, 9.2] }}
      dpr={[1, 1.65]}
      gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x071812, 0);
      }}
    >
      <ContextGuard onContextLost={onContextLost} />
      <ResponsiveStageCamera columnCount={stage.columns.length} />
      <ambientLight intensity={0.85} />
      <pointLight color="#a4e7c3" intensity={11} position={[-4, 4, 5]} />
      <pointLight color="#d6b77c" intensity={8} position={[4, -1, 4]} />
      <DustField daylight={daylight} frame={frame} />
      <group position={daylight ? [0, -0.72, 0] : [0, 0, 0]}>
        {stage.relations.map((relation) => (
          <NeutralRelationArc
            active={activeRelationRefs.has(relation.relation_ref)}
            boundary={frame.focus === "EVIDENCE_BOUNDARY"}
            daylight={daylight}
            frame={frame}
            key={relation.relation_ref}
            leftX={positionsByColumn.get(relation.left_column_ref) ?? 0}
            relation={relation}
            rightX={positionsByColumn.get(relation.right_column_ref) ?? 0}
          />
        ))}
        {placements.map(({ body, column, position }) => (
          <StageBody
            body={body}
            daylight={daylight}
            focused={isBodyFocused(
              body,
              column,
              frame,
              relationMemberColumnRefs,
              narratedColumnRefs,
            )}
            frame={frame}
            key={body.body_ref}
            position={position}
          />
        ))}
      </group>
    </Canvas>
  );
}

function ResponsiveStageCamera({ columnCount }: { columnCount: number }) {
  const camera = useThree((state) => state.camera);
  const size = useThree((state) => state.size);

  useEffect(() => {
    if (!(camera instanceof THREE.PerspectiveCamera)) return;
    const aspect = Math.max(size.width / Math.max(size.height, 1), 0.5);
    const requiredHalfWidth = columnCount === 6 ? 3.95 : 3;
    const halfVerticalFov = THREE.MathUtils.degToRad(camera.fov / 2);
    const fittedDistance =
      requiredHalfWidth / Math.max(Math.tan(halfVerticalFov) * aspect, 0.01);
    camera.position.set(0, 0.15, Math.max(9.2, Math.min(fittedDistance, 28)));
    camera.updateProjectionMatrix();
  }, [camera, columnCount, size.height, size.width]);

  return null;
}

function ContextGuard({ onContextLost }: { onContextLost: () => void }) {
  const gl = useThree((state) => state.gl);
  useEffect(() => {
    const canvas = gl.domElement;
    const handleLoss = (event: Event) => {
      event.preventDefault();
      onContextLost();
    };
    canvas.addEventListener("webglcontextlost", handleLoss);
    return () => canvas.removeEventListener("webglcontextlost", handleLoss);
  }, [gl, onContextLost]);
  return null;
}

function StageBody({
  body,
  daylight,
  focused,
  frame,
  position,
}: {
  body: MingliStageBody;
  daylight: boolean;
  focused: boolean;
  frame: MingliSceneFrame;
  position: [number, number, number];
}) {
  const groupRef = useRef<THREE.Group>(null);
  const membraneRef = useRef<THREE.MeshBasicMaterial>(null);
  const particleRef = useRef<THREE.Points>(null);
  const pointsRef = useRef<THREE.PointsMaterial>(null);
  const ambientSeconds = useRef(0);
  const color = (daylight ? DAYLIGHT_ELEMENT_COLORS : ELEMENT_COLORS)[body.glyph]
    ?? (daylight ? "#315d49" : "#b9d7c6");
  const particleGeometry = useMemo(
    () => particleShellGeometry(body.body_ref, 88),
    [body.body_ref],
  );
  const glyphTexture = useMemo(
    () => createGlyphTexture(body.glyph, daylight),
    [body.glyph, daylight],
  );

  useEffect(
    () => () => {
      particleGeometry.dispose();
      glyphTexture.dispose();
    },
    [glyphTexture, particleGeometry],
  );

  useFrame((_, delta) => {
    if (frame.ambientRunning) ambientSeconds.current += Math.min(delta, 0.05);
    const group = groupRef.current;
    if (!group) return;
    const ambient = Math.sin(ambientSeconds.current * 0.9 + body.order * 0.67);
    const semanticAmount = frame.cueProgress;
    const speechSeconds = frame.currentTimeMs / 1000;
    const speechPulse = frame.currentTimeMs > 0 || frame.semanticRunning
      ? (Math.sin(speechSeconds * 2.8 + body.order * 0.58) + 1) / 2
      : 0;
    const focusScale = focused
      ? 1 + semanticAmount * 0.055 + speechPulse * 0.038
      : 0.86;
    group.scale.setScalar(focusScale + ambient * 0.012);
    group.position.set(position[0], position[1] + ambient * 0.035, position[2]);
    if (particleRef.current) {
      particleRef.current.rotation.y = speechSeconds * 0.16 + body.order * 0.04;
      particleRef.current.rotation.x = ambient * 0.025;
    }
    if (membraneRef.current) {
      membraneRef.current.opacity = focused ? (daylight ? 0.24 : 0.34) : 0.12;
    }
    if (pointsRef.current) {
      pointsRef.current.opacity = focused ? (daylight ? 0.92 : 0.82) : 0.23;
      pointsRef.current.size = focused ? 0.031 + speechPulse * 0.006 : 0.024;
    }
  });

  return (
    <group name={body.body_ref} position={position} ref={groupRef}>
      <mesh>
        <sphereGeometry args={[0.48, 38, 38]} />
        <meshBasicMaterial
          color={color}
          depthWrite={false}
          opacity={0.16}
          ref={membraneRef}
          transparent
        />
      </mesh>
      <points geometry={particleGeometry} ref={particleRef}>
        <pointsMaterial
          blending={daylight ? THREE.NormalBlending : THREE.AdditiveBlending}
          color={color}
          depthWrite={false}
          opacity={0.82}
          ref={pointsRef}
          size={0.033}
          sizeAttenuation
          transparent
        />
      </points>
      <sprite scale={[0.54, 0.54, 1]}>
        <spriteMaterial
          depthTest={false}
          map={glyphTexture}
          opacity={0.96}
          transparent
        />
      </sprite>
    </group>
  );
}

function NeutralRelationArc({
  active,
  boundary,
  daylight,
  frame,
  leftX,
  relation,
  rightX,
}: {
  active: boolean;
  boundary: boolean;
  daylight: boolean;
  frame: MingliSceneFrame;
  leftX: number;
  relation: MingliStageRelation;
  rightX: number;
}) {
  const geometry = useMemo(() => {
    const distance = Math.abs(rightX - leftX);
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(leftX, -0.9, -0.08),
      new THREE.Vector3((leftX + rightX) / 2, -0.9 + distance * 0.42, 0.03),
      new THREE.Vector3(rightX, -0.9, -0.08),
    );
    return new THREE.BufferGeometry().setFromPoints(curve.getPoints(44));
  }, [leftX, rightX]);
  const material = useMemo(
    () =>
      new THREE.LineBasicMaterial({
        color: daylight
          ? boundary ? "#725b28" : "#2f6b52"
          : boundary ? "#cbbd91" : "#86ccb0",
        depthWrite: false,
        opacity: active ? 0.5 : 0.1,
        transparent: true,
      }),
    [active, boundary, daylight],
  );
  const line = useMemo(() => new THREE.Line(geometry, material), [geometry, material]);

  useEffect(
    () => () => {
      geometry.dispose();
      material.dispose();
    },
    [geometry, material],
  );
  useFrame(() => {
    const semanticAmount = frame.cueProgress;
    material.opacity = active
      ? boundary
        ? 0.46
        : 0.5 + semanticAmount * 0.36
      : 0.1;
  });

  line.name = relation.relation_ref;
  return <primitive object={line} />;
}

function DustField({
  daylight,
  frame,
}: {
  daylight: boolean;
  frame: MingliSceneFrame;
}) {
  const pointsRef = useRef<THREE.Points>(null);
  const ambientSeconds = useRef(0);
  const geometry = useMemo(() => {
    const positions = new Float32Array(330 * 3);
    for (let index = 0; index < 330; index += 1) {
      const seed = seededUnit(index + 971);
      positions[index * 3] = (seededUnit(index * 3 + 17) - 0.5) * 12;
      positions[index * 3 + 1] = (seededUnit(index * 7 + 29) - 0.5) * 6.2;
      positions[index * 3 + 2] = -1.3 - seed * 3.2;
    }
    const value = new THREE.BufferGeometry();
    value.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return value;
  }, []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  useFrame((_, delta) => {
    if (frame.ambientRunning) ambientSeconds.current += Math.min(delta, 0.05);
    if (pointsRef.current) pointsRef.current.rotation.z = ambientSeconds.current * 0.012;
  });
  return (
    <points geometry={geometry} ref={pointsRef}>
      <pointsMaterial
        blending={daylight ? THREE.NormalBlending : THREE.AdditiveBlending}
        color={daylight ? "#315d49" : "#d5e7d9"}
        depthWrite={false}
        opacity={daylight ? 0.12 : 0.22}
        size={0.018}
        transparent
      />
    </points>
  );
}

function placeBodies(stage: MingliStageProjection): BodyPlacement[] {
  const columns = new Map(stage.columns.map((column) => [column.column_ref, column]));
  return stage.bodies.map((body) => {
    const column = columns.get(body.column_ref);
    if (!column) throw new Error(`UNKNOWN_MINGLI_STAGE_COLUMN:${body.column_ref}`);
    const index = stage.columns.findIndex(
      (candidate) => candidate.column_ref === body.column_ref,
    );
    return {
      body,
      column,
      position: [
        columnX(index, stage.columns.length),
        body.role === "STEM" ? 0.72 : -0.72,
        column.source_layer === "NATAL" ? 0 : -0.08,
      ],
    };
  });
}

function columnX(index: number, count: number) {
  const spacing = count === 6 ? 1.28 : 1.58;
  return (index - (count - 1) / 2) * spacing;
}

function relationColumnRefs(
  stage: MingliStageProjection,
  relationRefs: Set<string>,
) {
  const refs = new Set<string>();
  stage.relations.forEach((relation) => {
    if (!relationRefs.has(relation.relation_ref)) return;
    refs.add(relation.left_column_ref);
    refs.add(relation.right_column_ref);
  });
  return refs;
}

function isBodyFocused(
  body: MingliStageBody,
  column: MingliStageColumn,
  frame: MingliSceneFrame,
  relationMemberColumnRefs: Set<string>,
  narratedColumnRefs: Set<string>,
) {
  if (narratedColumnRefs.size > 0) {
    return narratedColumnRefs.has(column.column_ref);
  }
  if (frame.focus === "ALL_PILLARS") return true;
  if (frame.focus === "TIME_LAYER") return column.source_layer !== "NATAL";
  return body.role === "BRANCH" && relationMemberColumnRefs.has(column.column_ref);
}

function particleShellGeometry(key: string, count: number) {
  const positions = new Float32Array(count * 3);
  const offset = Array.from(key).reduce((sum, character) => sum + character.charCodeAt(0), 0);
  for (let index = 0; index < count; index += 1) {
    const y = 1 - (index / Math.max(1, count - 1)) * 2;
    const radius = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = index * Math.PI * (3 - Math.sqrt(5)) + offset * 0.017;
    const shell = 0.5 + seededUnit(index + offset) * 0.08;
    positions[index * 3] = Math.cos(theta) * radius * shell;
    positions[index * 3 + 1] = y * shell;
    positions[index * 3 + 2] = Math.sin(theta) * radius * shell;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  return geometry;
}

function seededUnit(seed: number) {
  const value = Math.sin(seed * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function createGlyphTexture(glyph: string, daylight: boolean) {
  const canvas = document.createElement("canvas");
  canvas.width = 192;
  canvas.height = 192;
  const context = canvas.getContext("2d");
  if (context) {
    context.clearRect(0, 0, 192, 192);
    context.font = "500 104px 'Songti SC', 'Noto Serif SC', serif";
    context.textAlign = "center";
    context.textBaseline = "middle";
    if (daylight) {
      context.lineWidth = 8;
      context.strokeStyle = "rgba(250, 246, 222, 0.9)";
      context.strokeText(glyph, 96, 104);
      context.fillStyle = "rgba(20, 58, 40, 0.98)";
    } else {
      context.fillStyle = "rgba(246, 240, 215, 0.98)";
    }
    context.fillText(glyph, 96, 104);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}
