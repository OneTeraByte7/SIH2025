import React from 'react';
import { Zap, Activity, Satellite } from 'lucide-react';
import './App.css';

const droneImages = [
  {
    src: '/1.jpg',
    caption: 'Hypersonic interceptor squadron establishing an aerial shield.',
  },
  {
    src: '/2.jpg',
    caption: 'Autonomous tactical drone performing realtime terrain mapping.',
  },
  {
    src: '/3.jpg',
    caption: 'Swarm intelligence harmonising multi-axis defence lanes.',
  },
];

const LandingPage = ({ onDismiss, isExiting }) => {
  return (
    <div
      className={`landing-page ${isExiting ? 'landing-page--exit' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="landing-title"
      onClick={onDismiss}
    >
      <div className="landing-page__backdrop" />
      <div className="landing-page__content" onClick={(event) => event.stopPropagation()}>
        <div className="landing-page__glow" />
        <header className="landing-page__header">
          <div className="landing-page__badge">
            <Zap className="landing-page__badge-icon" />
            QIPFD Core Initiative
          </div>
          <h1 id="landing-title" className="landing-page__title">
            AeroSentinel
          </h1>
          <p className="landing-page__subtitle">
            Quantum-Inspired Probabilistic Field   Defence (QIPFD) orchestrating predictive response corridors across contested airspace.
          </p>
        </header>

        <p className="landing-page__mission">
          Step inside our command lattice to watch multi-agent swarms neutralise adaptive threats in real time. The AeroSentinel fuses predictive AI with tactical telemetry to choreograph defender drones, asset guardians, and pursuit hunters in a living battlescape.
        </p>

        <div className="landing-page__grid" role="list">
          {droneImages.map((image) => (
            <figure key={image.src} className="landing-page__card" role="listitem">
              <img src={image.src} alt={image.caption} className="landing-page__image" loading="lazy" />
              <figcaption className="landing-page__caption">
                <Satellite className="landing-page__caption-icon" />
                {image.caption}
              </figcaption>
            </figure>
          ))}
        </div>

        <button type="button" className="landing-page__cta" onClick={onDismiss}>
          <span>Launch Command Center</span>
          <Activity className="landing-page__cta-icon" />
        </button>
      </div>
    </div>
  );
};

export default LandingPage;
