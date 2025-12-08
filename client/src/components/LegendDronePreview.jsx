import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { createDroneModel } from '../three/createDroneModel.js';

const LegendDronePreview = ({
    color,
    accent,
    propellerColor,
    showLandingSkids = false
}) => {
    const mountRef = useRef(null);
    const animationRef = useRef(null);
    const rendererRef = useRef(null);
    const sceneRef = useRef(null);
    const propellersRef = useRef([]);
    const droneGroupRef = useRef(null);

    useEffect(() => {
        const mount = mountRef.current;
        if (!mount) return undefined;

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x03050a);
        sceneRef.current = scene;

        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
        camera.position.set(25, 20, 30);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(mount.clientWidth || 72, mount.clientHeight || 72);
        mount.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambient);
        const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
        keyLight.position.set(40, 50, 20);
        scene.add(keyLight);
        const rimLight = new THREE.PointLight(0x2ec6ff, 0.7, 120);
        rimLight.position.set(-20, 10, -18);
        scene.add(rimLight);

        const { group, propellers } = createDroneModel({
            color,
            accent,
            propellerColor,
            scale: 0.45,
            showLandingSkids
        });
        group.position.y = 2;
        group.rotation.y = Math.PI / 4;
        scene.add(group);
        droneGroupRef.current = group;
        propellersRef.current = propellers;

        const animate = () => {
            animationRef.current = requestAnimationFrame(animate);
            if (droneGroupRef.current) {
                droneGroupRef.current.rotation.y += 0.009;
                droneGroupRef.current.position.y = 2 + Math.sin(Date.now() * 0.003) * 0.35;
            }
            propellersRef.current.forEach(prop => {
                prop.rotation.y += prop.userData.spinSpeed ?? 0.35;
            });
            renderer.render(scene, camera);
        };
        animate();

        const resizeObserver = typeof ResizeObserver !== 'undefined'
            ? new ResizeObserver(entries => {
                const entry = entries[0];
                if (!entry) return;
                const size = Math.min(entry.contentRect.width, entry.contentRect.height);
                renderer.setSize(size, size);
                camera.aspect = 1;
                camera.updateProjectionMatrix();
            })
            : null;
        resizeObserver?.observe(mount);

        return () => {
            resizeObserver?.disconnect();
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
            propellersRef.current = [];
            if (rendererRef.current) {
                rendererRef.current.dispose();
                if (rendererRef.current.domElement?.parentNode === mount) {
                    rendererRef.current.domElement.remove();
                }
            }
            scene.traverse(obj => {
                if (obj.geometry) obj.geometry.dispose();
                if (obj.material) {
                    if (Array.isArray(obj.material)) {
                        obj.material.forEach(mat => mat?.dispose?.());
                    } else {
                        obj.material.dispose?.();
                    }
                }
            });
        };
    }, [accent, color, propellerColor, showLandingSkids]);

    return <div className="legend-drone-preview" ref={mountRef} />;
};

export default LegendDronePreview;
