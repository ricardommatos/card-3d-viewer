// Watch — a Texture by Textures · https://textures.dev/s/watch
// Install another: npx shadcn@latest add https://textures.dev/r/<slug>.json
// For agents: https://textures.md
// License: free to use
"use client"
import { type CSSProperties, useEffect, useId, useRef } from "react"
function selfSize(root: HTMLElement | null): void {
	const host = root?.parentElement
	if (!root || !host || host.getBoundingClientRect().height > 0) return
	root.style.minHeight = "240px"
}
type Pointer = { x: number; y: number; active: number; reduced: boolean }
const AMBIENT_SPEED = 1.5
const AMBIENT_CYCLE = 4.5
type EngineOptions = { ambientSpeed?: number }
function engine(
	root: HTMLElement,
	draw: (p: Pointer, dt: number) => boolean | void,
	min: [number, number],
	options: EngineOptions = {},
): () => void {
	const svg = root.querySelector("svg")
	if (!svg) return () => {}
	const mq = () => matchMedia("(prefers-reduced-motion: reduce)").matches || matchMedia("(update: slow)").matches
	const touchMq = matchMedia("(hover: none), (pointer: coarse)")
	const forced = () => root.closest("[data-motion]")?.getAttribute("data-motion") ?? null
	const wantsAmbient = () => (forced() ? forced() === "ambient" : touchMq.matches)
	const speed = AMBIENT_SPEED * (options.ambientSpeed ?? 1)
	const w = (2 * Math.PI) / AMBIENT_CYCLE
	const phase = Math.random() * 2 * Math.PI
	let onScreen = false
	let ambient = false
	let clock = 0
	let hold = 0
	let box: { left: number; top: number; s: number; ox: number; oy: number } | null = null
	let px = 366
	let py = 258
	let cx = 0
	let cy = 0
	let active = 0
	let target = 0
	let vel = 0
	let frame = 0
	let last = 0
	let lastMoveAt = 0
	const measure = () => {
		const r = svg.getBoundingClientRect()
		if (r.width < min[0] || r.height < min[1]) {
			box = null
			return
		}
		const s = Math.max(r.width / 732, r.height / 516)
		box = { left: r.left, top: r.top, s, ox: (r.width - 732 * s) / 2, oy: (r.height - 516 * s) / 2 }
	}
	const tick = (now: number) => {
		const dt = Math.min(last ? (now - last) / 1000 : 1 / 60, 1 / 30)
		last = now
		let moving = false
		const reduced = mq()
		if (ambient && now > hold) {
			if (reduced) target = 0
			else {
				clock += dt * speed
				const t = clock
				px = 366 + 366 * (0.76 * Math.sin(w * t + phase) + 0.2 * Math.sin(1.93 * w * t + 1.2 + phase))
				py = 258 + 258 * (0.72 * Math.sin(0.75 * w * t + 0.8 + phase) + 0.2 * Math.sin(1.37 * w * t + 2.1 + phase))
				target = 1
				moving = true
			}
		}
		if (reduced) {
			active = target
			vel = 0
		} else {
			const decay = Math.exp(-30 * dt)
			const off = active - target
			const lead = vel + 30 * off
			active = target + (off + lead * dt) * decay
			vel = (vel - 30 * lead * dt) * decay
			if (Math.abs(vel) < 0.02 && Math.abs(active - target) < 0.02) {
				active = target
				vel = 0
			} else moving = true
		}
		const more = draw({ x: px, y: py, active, reduced }, dt)
		if (moving || more) frame = requestAnimationFrame(tick)
		else {
			frame = 0
			last = 0
		}
	}
	const wake = () => {
		if (!frame) frame = requestAnimationFrame(tick)
	}
	const touchIsAmbient = (e: Event) => (e as PointerEvent).pointerType === "touch" && touchMq.matches
	const onEnter = (e: PointerEvent) => {
		if (touchIsAmbient(e)) return
		measure()
	}
	const onMove = (e: PointerEvent) => {
		if (touchIsAmbient(e)) return
		const t = performance.now()
		if (!box || t - lastMoveAt > 250) measure()
		lastMoveAt = t
		if (!box) return
		if (!e.isTrusted) hold = performance.now() + 1000
		cx = e.clientX
		cy = e.clientY
		px = (cx - box.left - box.ox) / box.s
		py = (cy - box.top - box.oy) / box.s
		target = 1
		wake()
	}
	const onLeave = (e?: Event) => {
		if (e && touchIsAmbient(e)) return
		if (e && !e.isTrusted) hold = 0
		if (ambient && performance.now() > hold) return
		target = 0
		wake()
	}
	const onFocus = () => {
		measure()
		if (!box) return
		px = 366
		py = 258
		target = 1
		wake()
	}
	const onResize = () => {
		if (box || ambient) measure()
		if (ambient && !box) ambient = false
		settle()
	}
	const onScroll = () => {
		if (!box || target !== 1 || (ambient && performance.now() > hold)) return
		measure()
		if (!box) return
		px = (cx - box.left - box.ox) / box.s
		py = (cy - box.top - box.oy) / box.s
		wake()
	}
	const settle = () => {
		const next = onScreen && !document.hidden && wantsAmbient()
		if (next === ambient) return
		ambient = next
		if (ambient) {
			measure()
			if (!box) {
				ambient = false
				return
			}
			wake()
		} else {
			target = 0
			wake()
		}
	}
	const io =
		typeof IntersectionObserver === "function"
			? new IntersectionObserver(
					([entry]) => {
						onScreen = !!entry?.isIntersecting
						settle()
					},
					{ threshold: 0.2 },
				)
			: null
	io?.observe(svg)
	if (!io) {
		onScreen = true
		settle()
	}
	const onVisibility = () => settle()
	const onCapability = () => settle()
	const reducedMq = matchMedia("(prefers-reduced-motion: reduce)")
	const onReduced = () => wake()
	document.addEventListener("visibilitychange", onVisibility)
	touchMq.addEventListener?.("change", onCapability)
	reducedMq.addEventListener?.("change", onReduced)
	const host: Element = root.closest("a, button, [tabindex]") ?? root.parentElement ?? root
	root.addEventListener("pointerenter", onEnter)
	root.addEventListener("pointermove", onMove, { passive: true })
	root.addEventListener("pointerleave", onLeave)
	root.addEventListener("pointercancel", onLeave)
	host.addEventListener("focusin", onFocus)
	host.addEventListener("focusout", onLeave)
	window.addEventListener("resize", onResize, { passive: true })
	window.addEventListener("scroll", onScroll, { passive: true, capture: true })
	return () => {
		root.removeEventListener("pointerenter", onEnter)
		root.removeEventListener("pointermove", onMove)
		root.removeEventListener("pointerleave", onLeave)
		root.removeEventListener("pointercancel", onLeave)
		host.removeEventListener("focusin", onFocus)
		host.removeEventListener("focusout", onLeave)
		window.removeEventListener("resize", onResize)
		window.removeEventListener("scroll", onScroll, { capture: true })
		document.removeEventListener("visibilitychange", onVisibility)
		touchMq.removeEventListener?.("change", onCapability)
		reducedMq.removeEventListener?.("change", onReduced)
		io?.disconnect()
		if (frame) cancelAnimationFrame(frame)
	}
}
const W = 732
const H = 516
const COLS = 27
const ROWS = 19
const CELL = 23.58
const PITCH = 26.08
const X0 = 15
const Y0 = 11.49
const DIM = 0.1
const SIZES: number[] = [23.6, 22.8, 21.65, 19.77, 16.95, 11.3, 9.4, 7.5, 5.6, 3.77]
const S_MIN = 3.77
const EYE = 0.85
const EYE_REACH = 14
const TAU_NEAR = 0.045
const TAU_FAR = 0.14
export type WatchProps = {
	tokens?: Partial<Record<"--texture-ink" | "--texture-field", string>>
	className?: string
	static?: boolean
}
const N = COLS * ROWS
const REST = S_MIN / CELL
const sizeAt = (d: number) => {
	const i = Math.min(SIZES.length - 1, d)
	const k = Math.floor(i)
	const f = i - k
	return k >= SIZES.length - 1 ? SIZES[SIZES.length - 1]! : SIZES[k]! * (1 - f) + SIZES[k + 1]! * f
}
export function Watch({ tokens, className = "", static: isStatic = false }: WatchProps) {
	const ref = useRef<HTMLDivElement>(null)
	useEffect(() => selfSize(ref.current), [])
	const squares = useRef<(SVGRectElement | null)[]>([])
	const uid = useId().replace(/[^a-zA-Z0-9]/g, "")
	const patternId = `watch-cells-${uid}`
	useEffect(() => {
		const root = ref.current
		if (!root || isStatic) return
		const size = new Float32Array(N).fill(S_MIN)
		const ox = new Float32Array(N)
		const oy = new Float32Array(N)
		const written = new Float32Array(N * 3).fill(Infinity)
		return engine(
			root,
			({ x, y, active, reduced }, dt) => {
				let moving = false
				const cx = (x - X0 - CELL / 2) / PITCH
				const cy = (y - Y0 - CELL / 2) / PITCH
				for (let i = 0; i < N; i++) {
					const c = i % COLS
					const r = Math.floor(i / COLS)
					const dx = cx - c
					const dy = cy - r
					const d = Math.hypot(dx, dy)
					const wantSize = S_MIN + (sizeAt(d) - S_MIN) * active
					const room =
						((CELL - wantSize) / 2) * EYE * active * (d < EYE_REACH ? 1 : Math.max(0, 1 - (d - EYE_REACH) / 3))
					const wantX = d > 0.001 ? (dx / d) * room : 0
					const wantY = d > 0.001 ? (dy / d) * room : 0
					let s = size[i]!
					let px = ox[i]!
					let py = oy[i]!
					if (reduced) {
						s = wantSize
						px = wantX
						py = wantY
					} else {
						const tau = TAU_NEAR + (TAU_FAR - TAU_NEAR) * Math.min(1, d / EYE_REACH)
						const k = 1 - Math.exp(-dt / tau)
						s += (wantSize - s) * k
						px += (wantX - px) * k
						py += (wantY - py) * k
						if (Math.abs(s - wantSize) < 0.02 && Math.abs(px - wantX) < 0.02 && Math.abs(py - wantY) < 0.02) {
							s = wantSize
							px = wantX
							py = wantY
						} else moving = true
					}
					size[i] = s
					ox[i] = px
					oy[i] = py
					const j = i * 3
					const restNow = s === S_MIN && px === 0 && py === 0
					if (
						(restNow && (written[j] !== S_MIN || written[j + 1] !== 0 || written[j + 2] !== 0)) ||
						Math.abs(s - written[j]!) > 0.03 ||
						Math.abs(px - written[j + 1]!) > 0.1 ||
						Math.abs(py - written[j + 2]!) > 0.1
					) {
						written[j] = s
						written[j + 1] = px
						written[j + 2] = py
						const el = squares.current[i]
						if (el) {
							const sc = s / CELL
							el.style.transform =
								s === S_MIN && px === 0 && py === 0
									? `scale(${REST.toFixed(4)})`
									: `translate(${px.toFixed(2)}px, ${py.toFixed(2)}px) scale(${sc.toFixed(4)})`
						}
					}
				}
				return moving
			},
			[160, 112],
		)
	}, [isStatic])
	const style = {
		"--texture-ink": "var(--foreground)",
		"--texture-field": "var(--background)",
		...tokens,
		color: "var(--texture-ink)",
		background: "var(--texture-field)",
	} as CSSProperties
	return (
		<div
			ref={ref}
			style={{
				position: "relative",
				isolation: "isolate",
				height: "100%",
				width: "100%",
				overflow: "clip",
				contain: "layout paint style",
				containerType: "size",
				...style,
			}}
			data-texture="watch"
			className={className}
		>
			<svg
				viewBox={`0 0 ${W} ${H}`}
				preserveAspectRatio="xMidYMid slice"
				aria-hidden="true"
				focusable="false"
				fill="currentColor"
				style={{ position: "absolute", inset: 0, display: "block", height: "100%", width: "100%" }}
			>
				<defs>
					<pattern id={patternId} x={X0} y={Y0} width={PITCH} height={PITCH} patternUnits="userSpaceOnUse">
						<rect width={CELL} height={CELL} rx={CELL / 2} fillOpacity={DIM} />
					</pattern>
				</defs>
				<rect x={X0} y={Y0} width={COLS * PITCH} height={ROWS * PITCH} fill={`url(#${patternId})`} />
				{Array.from({ length: N }, (_, i) => (
					<rect
						key={i}
						ref={(el) => {
							squares.current[i] = el
						}}
						x={(X0 + (i % COLS) * PITCH).toFixed(2)}
						y={(Y0 + Math.floor(i / COLS) * PITCH).toFixed(2)}
						width={CELL}
						height={CELL}
						rx={CELL / 2}
						style={{ transformBox: "fill-box", transformOrigin: "center", transform: `scale(${REST.toFixed(4)})` }}
					/>
				))}
			</svg>
		</div>
	)
}
