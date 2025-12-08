import React, { useLayoutEffect } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import ScrollSmoother from 'gsap/ScrollSmoother';

import HeroSection from './components/HeroSection.jsx';
import ChallengeSection from './components/ChallengeSection.jsx';

gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

const LandingPage = ({ onLaunch }) => {
  useLayoutEffect(() => {
    const smoother = ScrollSmoother.create({
      wrapper: '#smooth-wrapper',
      content: '#smooth-content',
      smooth: 1.6,
      effects: true,
      smoothTouch: 0.1,
    });

    return () => {
      smoother?.kill();
    };
  }, []);

  return (
    <div id="smooth-wrapper" className="bg-black text-white">
      <div id="smooth-content">
        <HeroSection onLaunch={onLaunch} />
        <ChallengeSection />
      </div>
    </div>
  );
};

export default LandingPage;
