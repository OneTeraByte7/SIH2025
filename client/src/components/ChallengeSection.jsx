import React, { useLayoutEffect, useRef } from 'react'
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";
import redBlueDrone from "../assets/red-blue-drone.png";

gsap.registerPlugin(ScrollTrigger);

const ChallengeSection = () => {

    const droneRef = useRef(null);
    const sectionRef = useRef(null);

    useLayoutEffect(() => {
        const ctx = gsap.context(() => {

            gsap.fromTo(
                droneRef.current,
                { x: -500, opacity: 0, rotate: 30 },
                {
                    x: 0,
                    opacity: 1,
                    duration: 1.4,
                    rotate: 0,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: sectionRef.current,
                        start: "top 20%",
                        end: "top 60%",
                        toggleActions: "play none none none",

                    }
                }
            );

        }, sectionRef);

        return () => ctx.revert();
    }, []);

    return (
        <section
            ref={sectionRef}
            className='w-full relative px-10 bg-black'
        >

            <h2 className='font-gold text-white/60 text-7xl text-right pt-10 '>
                <span className='text-white'>Threats</span> evolve<br />
                faster than <span className='text-white'>humans</span><br />
                can <span className='text-white'>respond.</span>
            </h2>

            <div className='relative flex w-full h-auto justify-center mb-10'>

                {/* DRONE WITH SCROLL ANIMATION */}
                <img
                    ref={droneRef}
                    src={redBlueDrone}
                    className='w-[40%] z-10'
                />

                <div className='absolute top-0 left-[18%] flex gap-3 z-20'>
                    <div className='bg-gradient-to-r from-[#00bf8fa6] to-[#001510d7] w-[250px] h-[150px] font-gold text-5xl text-transparent rounded-tr-[2.5rem] rounded-bl-[2.5rem]'>.</div>
                    <div className='bg-gradient-to-r from-[#00bf8fa6] to-[#001510d7] w-[200px] h-[100px] font-gold text-5xl text-transparent rounded-tl-[2.5rem] rounded-br-[2.5rem]'>.</div>
                </div>

                <div className='absolute bottom-5 right-[25%] flex gap-3 z-0'>
                    <div className='bg-gradient-to-r from-[#00bf8fa6] to-[#001510d7] w-[100px] h-[100px] font-gold text-5xl text-transparent rounded-tr-[2.5rem] rounded-bl-[2.5rem]'>.</div>
                    <div className='bg-gradient-to-r from-[#001510d7] to-[#00bf8fa6] w-[200px] h-[100px] font-gold text-5xl text-transparent rounded-tl-[2.5rem] rounded-br-[2.5rem]'>.</div>
                </div>

            </div>

            <p className='font-pop text-white w-[40%] pb-10 font-light'>
                Modern battlefields demand instant decisions, precise coordination,
                and continuous adaptation — conditions where human operators and
                traditional defense systems fall behind.
            </p>

        </section>
    )
}

export default ChallengeSection
