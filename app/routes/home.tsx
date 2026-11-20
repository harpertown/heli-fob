import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Heli FOB — Flight Operations" },
		{
			name: "description",
			content: "Fly eight pixel-art rescue missions in Heli FOB.",
		},
	];
}

export default function Home() {
	return (
		<main className="flight-page">
			<header className="flight-header">
				<div className="identity">
					<span className="signal" aria-hidden="true" />
					<div>
						<p className="unit-label">COASTAL AIR SERVICE</p>
						<h1>Heli FOB</h1>
					</div>
				</div>
				<p className="briefing">Flight operations <span>—</span> 8 missions</p>
			</header>

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
			<p className="save-note">Mission progress and best landings save on this device.</p>
		</main>
	);
}
