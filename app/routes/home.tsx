import { useState } from "react";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Heli FOB — Flight Operations" },
		{
			name: "description",
			content: "A pixel-art helicopter campaign. Fly eight missions, cross rough seas, and bring everyone home.",
		},
	];
}

function PixelScene() {
	return (
		<svg className="pixel-scene" viewBox="0 0 640 400" role="img" aria-label="A rescue helicopter above a moonlit coast">
			<rect width="640" height="400" fill="#182d43" />
			<rect y="32" width="640" height="80" fill="#203e59" />
			<rect y="112" width="640" height="60" fill="#31556b" />
			<rect y="172" width="640" height="54" fill="#456878" />
			<rect x="468" y="38" width="56" height="8" fill="#f4c878" />
			<rect x="452" y="46" width="88" height="8" fill="#f4c878" />
			<rect x="444" y="54" width="96" height="24" fill="#f4c878" />
			<rect x="452" y="78" width="80" height="8" fill="#f4c878" />
			<rect x="468" y="86" width="48" height="8" fill="#f4c878" />
			<rect x="88" y="40" width="6" height="6" fill="#e8f1d0" />
			<rect x="154" y="76" width="4" height="4" fill="#e8f1d0" />
			<rect x="232" y="36" width="5" height="5" fill="#e8f1d0" />
			<rect x="578" y="118" width="5" height="5" fill="#e8f1d0" />
			<rect x="66" y="124" width="4" height="4" fill="#f4c878" />
			<rect x="300" y="86" width="5" height="5" fill="#e8f1d0" />
			<path d="M0 207h66v-14h24v-17h20v17h22v-28h22v28h30v-14h18v28h34v-20h20v20h33v-13h23v13h29v-25h20v25h35v-16h26v16h33v-24h24v24h43v-12h22v12h42v-27h25v27h18v37H0z" fill="#263e49" />
			<rect y="236" width="640" height="164" fill="#173f53" />
			<rect y="236" width="640" height="12" fill="#4d8790" />
			<rect x="0" y="260" width="640" height="6" fill="#25566a" />
			<rect x="0" y="300" width="640" height="5" fill="#25566a" />
			<rect x="0" y="348" width="640" height="7" fill="#25566a" />
			<path d="M0 242h84v8h40v-8h56v8h48v-8h66v8h50v-8h50v8h60v-8h48v8h45v-8h55v8h34v5H0z" fill="#83c6bc" />
			<rect x="46" y="278" width="106" height="4" fill="#65aeb0" />
			<rect x="204" y="320" width="66" height="4" fill="#65aeb0" />
			<rect x="424" y="286" width="132" height="4" fill="#65aeb0" />
			<rect x="96" y="356" width="184" height="4" fill="#65aeb0" />
			<path d="M400 216h166v8H400z" fill="#e4b454" />
			<path d="M414 224h8v20h-8zm132 0h8v20h-8z" fill="#e4b454" />
			<path d="M427 216v-8h112v8" fill="none" stroke="#f3d18b" strokeWidth="4" />
			<rect x="442" y="212" width="80" height="4" fill="#f3d18b" />
			{/* Pixel-built rescue helicopter */}
			<rect x="205" y="133" width="130" height="5" fill="#e8f1d0" />
			<rect x="256" y="138" width="7" height="21" fill="#d9e5d1" />
			<rect x="236" y="157" width="106" height="30" fill="#d3d9c7" />
			<rect x="220" y="164" width="16" height="18" fill="#d3d9c7" />
			<rect x="342" y="165" width="72" height="8" fill="#d3d9c7" />
			<rect x="402" y="157" width="9" height="23" fill="#d3d9c7" />
			<rect x="244" y="164" width="19" height="14" fill="#4f8b9a" />
			<rect x="264" y="164" width="14" height="14" fill="#4f8b9a" />
			<rect x="236" y="186" width="108" height="5" fill="#e8f1d0" />
			<rect x="252" y="191" width="6" height="11" fill="#e8f1d0" />
			<rect x="326" y="191" width="6" height="11" fill="#e8f1d0" />
			<rect x="247" y="200" width="88" height="4" fill="#e8f1d0" />
			<rect x="407" y="164" width="22" height="4" fill="#e8f1d0" />
			<rect x="417" y="152" width="4" height="27" fill="#e8f1d0" />
			<rect x="410" y="147" width="18" height="4" fill="#e8f1d0" />
			<rect x="263" y="125" width="5" height="8" fill="#e8f1d0" />
			<rect x="264" y="119" width="122" height="5" fill="#e8f1d0" />
			<rect x="278" y="107" width="68" height="5" fill="#f4c878" />
			<rect x="267" y="111" width="96" height="4" fill="#f4c878" />
			<rect x="174" y="151" width="24" height="4" fill="#f27c67" />
			<rect x="178" y="159" width="18" height="4" fill="#f27c67" />
			<rect x="96" y="214" width="7" height="18" fill="#79a477" />
			<rect x="88" y="206" width="23" height="8" fill="#79a477" />
			<rect x="572" y="197" width="8" height="27" fill="#79a477" />
			<rect x="561" y="186" width="30" height="11" fill="#79a477" />
		</svg>
	);
}

export default function Home() {
	const [launched, setLaunched] = useState(false);

	if (launched) {
		return (
			<main className="play-page">
				<div className="play-heading">
					<a href="/" onClick={(event) => { event.preventDefault(); setLaunched(false); }}>← Heli FOB</a>
					<span>COASTAL AIR SERVICE · FLIGHT OPERATIONS</span>
				</div>
				<section className="game-stage" aria-label="Heli FOB game">
					<div className="screen-frame">
						<pyxel-run root="/" name="main.py" gamepad="enabled" />
					</div>
				</section>
				<footer className="flight-controls" aria-label="Game controls">
					<div><kbd>↑</kbd><kbd>↓</kbd><span>Collective</span></div>
					<div><kbd>←</kbd><kbd>→</kbd><span>Cyclic</span></div>
					<div><kbd>Space</kbd><span>Continue / take off</span></div>
					<div><kbd>R</kbd><span>Restart mission</span></div>
				</footer>
			</main>
		);
	}

	return (
		<main className="splash-page">
			<header className="splash-topline">
				<a className="brand-mark" href="#top" aria-label="Heli FOB home"><span className="brand-pixel" /> HFOB</a>
				<span className="topline-status"><i /> FLIGHT CREW NEEDED</span>
			</header>

			<section className="splash-hero" id="top">
				<div className="hero-copy">
					<p className="eyebrow">COASTAL AIR SERVICE · 08 MISSIONS</p>
					<h1>HELI<br /><span>FOB</span></h1>
					<p className="hero-description">The coast is counting on you.<br />Fly low. Bring everyone home.</p>
					<button className="launch-button" onClick={() => setLaunched(true)}>
						<span className="button-glyph" aria-hidden="true">▶</span> START FLIGHT
					</button>
					<p className="launch-note">BEST WITH A KEYBOARD</p>
				</div>
				<div className="scene-frame"><PixelScene /><span className="scene-caption">RESCUE FLIGHT  /  03:47 PM</span></div>
			</section>

			<section className="mission-strip" aria-label="Campaign details">
				<div><span className="strip-label">FLIGHT PLAN</span><strong>8 missions</strong></div>
				<div><span className="strip-label">TERRAIN</span><strong>Coast · forest · city</strong></div>
				<div><span className="strip-label">CONTROLS</span><strong><kbd>↑↓</kbd> lift <kbd>←→</kbd> steer</strong></div>
				<div className="record-note"><span className="record-dot" /> Progress saves on this device</div>
			</section>
			<footer className="splash-footer"><span>HELI FOB / FLIGHT OPERATIONS</span><span>TAKE THE LONG WAY HOME</span></footer>
		</main>
	);
}
