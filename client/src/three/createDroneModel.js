import * as THREE from "three";

// Builds a high-fidelity quadcopter mesh and returns it with its propeller groups.
export const createDroneModel = ({
  color = 0x00aaff,
  accent = 0xffffff,
  propellerColor = 0x111111,
  scale = 1,
  showLandingSkids = false,
} = {}) => {
  const group = new THREE.Group();
  const propellers = [];

  const registerPropeller = (propGroup, spinSpeed = 0.35) => {
    propGroup.userData.spinSpeed = spinSpeed;
    propellers.push(propGroup);
  };

  const hullMat = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.55,
    roughness: 0.35,
    emissive: color,
    emissiveIntensity: 0.18,
  });
  const hull = new THREE.Mesh(
    new THREE.CylinderGeometry(12 * scale, 12 * scale, 6 * scale, 48),
    hullMat
  );
  hull.scale.set(1.18, 0.55, 1.18);
  group.add(hull);

  const canopy = new THREE.Mesh(
    new THREE.SphereGeometry(9 * scale, 32, 16),
    new THREE.MeshStandardMaterial({
      color: accent,
      metalness: 0.25,
      roughness: 0.2,
      emissive: accent,
      emissiveIntensity: 0.35,
    })
  );
  canopy.scale.set(1.05, 0.6, 1.05);
  canopy.position.y = 4 * scale;
  group.add(canopy);

  const intake = new THREE.Mesh(
    new THREE.ConeGeometry(2.6 * scale, 5 * scale, 24),
    new THREE.MeshStandardMaterial({
      color: 0x0d1018,
      metalness: 0.8,
      roughness: 0.3,
    })
  );
  intake.rotation.x = Math.PI / 2;
  intake.position.set(0, -1.5 * scale, 9 * scale);
  group.add(intake);

  const lens = new THREE.Mesh(
    new THREE.CircleGeometry(1.8 * scale, 24),
    new THREE.MeshStandardMaterial({
      color: 0x0f1c2b,
      emissive: 0x00c7ff,
      emissiveIntensity: 0.8,
      side: THREE.DoubleSide,
    })
  );
  lens.rotation.x = Math.PI / 2;
  lens.position.set(0, -1.5 * scale, 11.7 * scale);
  group.add(lens);

  const carbonMat = new THREE.MeshStandardMaterial({
    color: 0x1b212f,
    metalness: 0.15,
    roughness: 0.7,
  });
  const armGeo = new THREE.BoxGeometry(46 * scale, 2.6 * scale, 5 * scale);
  const xArm = new THREE.Mesh(armGeo, carbonMat);
  xArm.position.y = 0.5 * scale;
  group.add(xArm);
  const zArm = xArm.clone();
  zArm.rotation.y = Math.PI / 2;
  group.add(zArm);

  const ventRing = new THREE.Mesh(
    new THREE.TorusGeometry(8 * scale, 0.5 * scale, 16, 48),
    new THREE.MeshStandardMaterial({
      color: accent,
      emissive: accent,
      emissiveIntensity: 0.15,
    })
  );
  ventRing.rotation.x = Math.PI / 2;
  ventRing.position.y = 2.5 * scale;
  group.add(ventRing);

  const motorGeo = new THREE.CylinderGeometry(
    4.5 * scale,
    4.5 * scale,
    5 * scale,
    24
  );
  const motorMat = new THREE.MeshStandardMaterial({
    color: accent,
    metalness: 0.6,
    roughness: 0.25,
  });
  const guardGeo = new THREE.TorusGeometry(11 * scale, 0.6 * scale, 18, 48);
  const guardMat = new THREE.MeshStandardMaterial({
    color: 0x202a40,
    metalness: 0.2,
    roughness: 0.6,
  });
  const bladeGeo = new THREE.BoxGeometry(20 * scale, 0.5 * scale, 1.6 * scale);
  const bladeMat = new THREE.MeshStandardMaterial({
    color: propellerColor,
    metalness: 0.2,
    roughness: 0.4,
  });
  const navLightGeo = new THREE.SphereGeometry(1.1 * scale, 12, 12);
  const navLightMatFront = new THREE.MeshStandardMaterial({
    color: 0x00ffba,
    emissive: 0x00ffba,
    emissiveIntensity: 0.9,
  });
  const navLightMatRear = new THREE.MeshStandardMaterial({
    color: 0xff5577,
    emissive: 0xff5577,
    emissiveIntensity: 0.9,
  });

  const motorOffsets = [
    [30, 0, 30],
    [-30, 0, 30],
    [30, 0, -30],
    [-30, 0, -30],
  ];
  motorOffsets.forEach(([x, _y, z], index) => {
    const motorBase = new THREE.Mesh(motorGeo, motorMat);
    motorBase.position.set(x * scale, 3.5 * scale, z * scale);
    group.add(motorBase);

    const guard = new THREE.Mesh(guardGeo, guardMat);
    guard.position.set(x * scale, 4.5 * scale, z * scale);
    guard.rotation.x = Math.PI / 2;
    group.add(guard);

    const propGroup = new THREE.Group();
    propGroup.position.set(x * scale, 5 * scale, z * scale);
    for (let i = 0; i < 3; i += 1) {
      const blade = new THREE.Mesh(bladeGeo, bladeMat);
      blade.rotation.y = (Math.PI * 2 * i) / 3;
      propGroup.add(blade);
    }
    registerPropeller(propGroup, 0.3 + (index % 2) * 0.08);
    group.add(propGroup);

    const navLight = new THREE.Mesh(
      navLightGeo,
      index % 2 === 0 ? navLightMatFront : navLightMatRear
    );
    navLight.position.set(x * scale, 6.2 * scale, z * scale);
    group.add(navLight);
  });

  if (showLandingSkids) {
    const skidStrutGeo = new THREE.CylinderGeometry(
      0.9 * scale,
      0.9 * scale,
      12 * scale,
      10
    );
    const skidRailGeo = new THREE.CylinderGeometry(
      0.6 * scale,
      0.6 * scale,
      28 * scale,
      10
    );
    const skidMat = new THREE.MeshStandardMaterial({
      color: accent,
      roughness: 0.6,
    });
    [-8, 8].forEach((offsetZ) => {
      const strut = new THREE.Mesh(skidStrutGeo, skidMat);
      strut.rotation.x = Math.PI / 2;
      strut.position.set(offsetZ * 0.8 * scale, -4 * scale, offsetZ * scale);
      group.add(strut);

      const rail = new THREE.Mesh(skidRailGeo, skidMat);
      rail.rotation.z = Math.PI / 2;
      rail.position.set(offsetZ * 0.8 * scale, -6 * scale, offsetZ * scale);
      group.add(rail);
    });
  }

  return { group, propellers };
};
