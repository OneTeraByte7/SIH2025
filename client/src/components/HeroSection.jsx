import React, { useLayoutEffect, useRef } from 'react'
import gsap from "gsap";
import SplitText from "gsap/SplitText"; // requires GSAP Club plugin

import heroBgImg from "../assets/hero-section-bg.png";
import whiteDroneImg from "../assets/white-drone.png";

gsap.registerPlugin(SplitText);

const HeroSection = ({ onLaunch }) => {

    const titleRef = useRef(null);
    const droneRef = useRef(null);

    useLayoutEffect(() => {
        const ctx = gsap.context(() => {

            // Split text initially
            const split = new SplitText(titleRef.current, { type: "lines" });

            // -------------------------
            // 🌟 MASTER TIMELINE
            // -------------------------
            const tl = gsap.timeline({
                defaults: { ease: "power3.out" }
            });

            // 1️⃣ Drone fades in first
            tl.fromTo(
                droneRef.current,
                { opacity: 0 },
                {
                    opacity: 1,
                    duration: 1.4,
                    ease: "power3",
                    delay: 0.5
                }
            );

            // 2️⃣ THEN text lines animate
            tl.from(
                split.lines,
                {
                    rotationX: -100,
                    transformOrigin: "50% 50% -160px",
                    opacity: 0,
                    duration: 0.8,
                    stagger: 0.2,
                    ease: "power3"
                },
                "-=0.3" // overlaps slightly for smoother feel
            );

        });

        return () => ctx.revert();
    }, []);

    return (
        <section
            className='w-full min-h-screen relative px-10 overflow-hidden'
            style={{
                backgroundImage: `url(${heroBgImg})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
            }}
        >
            {/* Top Logo */}
            <h3 className='font-audio text-white w-full text-center text-2xl pt-3'>
                Swarm<span className='text-accent'>X</span>
            </h3>

            {/* RIGHT-SIDE WHITE DRONE */}
            <img
                ref={droneRef}
                src={whiteDroneImg}
                alt="drone"
                className='absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-[50%] opacity-90'
            />

            {/* HERO TEXT */}
            <div className='pt-20 relative z-10 w-[60%]'>
                <h2
                    ref={titleRef}
                    className='font-gold text-white leading-[70px] text-7xl'
                >
                    Real-Time <span className='text-accent'>Intelligence</span>.<br />
                    Real-Time <span className='text-accent'>Control.</span>
                </h2>

                <button
                    className='mt-7 font-pop relative text-white text-left pl-5 font-semibold h-12 w-60 bg-gradient-to-r from-[#00BF8F] to-[#001510] border border-white rounded-full hover:opacity-60'
                    onClick={onLaunch}
                >
                    Launch Simulation<span className=' buttonbefore '></span>
                </button>
            </div>

            <div className='w-[40%] font-pop mt-10 flex flex-col gap-5'>
                <div className='flex gap-4'>
                    <p className='bg-white/10 backdrop-blur-xl border border-white rounded-tl-[2.5rem] rounded-br-[2.5rem] p-4 text-white font-light' >
                        A next-generation swarm system that senses threats, adapts instantly, and visualizes every move with live battle analytics.
                    </p>
                    <p className='bg-gradient-to-r from-[#00bf8fa6] to-[#001510d7] w-[250px] font-gold text-5xl text-white flex justify-center items-center rounded-tr-[2.5rem] rounded-bl-[2.5rem]' >
                        4+
                    </p>
                </div>

                <div className='flex gap-4'>
                    <p className='bg-gradient-to-r from-[#00bf8fa6] to-[#001510d7] w-[250px] font-gold text-5xl text-white flex justify-center items-center rounded-tr-[2.5rem] rounded-bl-[2.5rem]'>
                        3D
                    </p>
                    <p className='bg-white/10 backdrop-blur-xl border border-white rounded-tl-[2.5rem] rounded-br-[2.5rem] p-4 text-white font-light'>
                        Watch autonomous drones coordinate, engage, and outsmart threats using quantum-inspired AI and real-time 3D simulation.
                    </p>
                </div>
            </div>
        </section>
    )
}

export default HeroSection
