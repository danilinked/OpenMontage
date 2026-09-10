import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/**
 * Dimension-line overlay for "how to measure it" explainers.
 *
 * Draws an animated cota (extension lines + arrowed dimension line + label)
 * over the background image the cut already provides, and can shade a region
 * that must be EXCLUDED from the measurement — a caravan drawbar, a tow bar,
 * a bike rack — with a red wash and a cross.
 *
 * All geometry is expressed in percentages of the frame so a cut can be
 * re-pointed at a different photo without touching pixel maths.
 */
interface MeasureSceneProps {
  /** "horizontal" measures left-to-right, "vertical" measures bottom-to-top. */
  orientation?: "horizontal" | "vertical";
  /** Start of the measured span, in % of frame width (h) or height (v). */
  from?: number;
  /** End of the measured span, same units as `from`. */
  to?: number;
  /** Where the dimension line sits on the other axis, in % of the frame. */
  offset?: number;
  /** Text that pops on the dimension line once it finishes drawing. */
  label?: string;
  /** Small uppercase step marker, e.g. "1. MIDE EL LARGO". */
  kicker?: string;
  /** Start of the excluded region, in the same units as `from`. */
  excludeFrom?: number;
  /** End of the excluded region. Omit the pair to shade nothing. */
  excludeTo?: number;
  /** Caption under the cross, e.g. "LA LANZA NO CUENTA". */
  excludeLabel?: string;
  accentColor?: string;
  excludeColor?: string;
  textColor?: string;
}

const LINE = 8;

export const MeasureScene: React.FC<MeasureSceneProps> = ({
  orientation = "horizontal",
  from = 10,
  to = 90,
  offset = 82,
  label,
  kicker,
  excludeFrom,
  excludeTo,
  excludeLabel,
  accentColor = "#137C61",
  excludeColor = "#E2231A",
  textColor = "#0F2E27",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const horizontal = orientation === "horizontal";
  const span = Math.abs(to - from);
  const start = Math.min(from, to);

  // The cota draws itself first, then the label lands, then the exclusion
  // wash fades in — so the eye reads "this is the measurement" before it
  // reads "and this part is not part of it".
  const draw = spring({ frame, fps, config: { damping: 22, stiffness: 70 } });
  const labelPop = spring({ frame: frame - 20, fps, config: { damping: 13, stiffness: 150 } });
  const excludePop = spring({ frame: frame - 32, fps, config: { damping: 16, stiffness: 120 } });
  const kickerRise = spring({ frame: frame - 4, fps, config: { damping: 18, stiffness: 110 } });

  const drawnSpan = span * draw;

  // Extension lines (the short perpendicular ticks at each end of the cota).
  const tick = (atPct: number, visible: number) => ({
    position: "absolute" as const,
    backgroundColor: accentColor,
    opacity: visible,
    borderRadius: LINE / 2,
    ...(horizontal
      ? {
          left: `${atPct}%`,
          top: `${offset - 4}%`,
          width: LINE,
          height: "8%",
          marginLeft: -LINE / 2,
        }
      : {
          top: `${atPct}%`,
          left: `${offset - 4}%`,
          height: LINE,
          width: "8%",
          marginTop: -LINE / 2,
        }),
  });

  return (
    <AbsoluteFill>
      {/* Excluded region — red wash plus a cross, e.g. the drawbar */}
      {excludeFrom !== undefined && excludeTo !== undefined && (
        <div
          style={{
            position: "absolute",
            opacity: excludePop * 0.55,
            backgroundColor: excludeColor,
            mixBlendMode: "multiply",
            ...(horizontal
              ? {
                  left: `${Math.min(excludeFrom, excludeTo)}%`,
                  width: `${Math.abs(excludeTo - excludeFrom)}%`,
                  top: 0,
                  bottom: 0,
                }
              : {
                  top: `${Math.min(excludeFrom, excludeTo)}%`,
                  height: `${Math.abs(excludeTo - excludeFrom)}%`,
                  left: 0,
                  right: 0,
                }),
          }}
        />
      )}

      {excludeFrom !== undefined && excludeTo !== undefined && (
        <div
          style={{
            position: "absolute",
            left: horizontal ? `${(excludeFrom + excludeTo) / 2}%` : "50%",
            top: horizontal ? "46%" : `${(excludeFrom + excludeTo) / 2}%`,
            transform: `translate(-50%, -50%) scale(${excludePop})`,
            fontFamily: "Inter, system-ui, sans-serif",
            fontSize: 190,
            fontWeight: 900,
            lineHeight: 1,
            color: excludeColor,
            textShadow: "0 6px 24px rgba(0,0,0,0.35)",
          }}
        >
          ✕
        </div>
      )}

      {/* Dimension line */}
      <div
        style={{
          position: "absolute",
          backgroundColor: accentColor,
          borderRadius: LINE / 2,
          boxShadow: "0 4px 18px rgba(0,0,0,0.28)",
          ...(horizontal
            ? {
                left: `${start}%`,
                width: `${drawnSpan}%`,
                top: `${offset}%`,
                height: LINE,
              }
            : {
                top: `${start}%`,
                height: `${drawnSpan}%`,
                left: `${offset}%`,
                width: LINE,
              }),
        }}
      />

      <div style={tick(from, draw)} />
      <div style={tick(to, draw > 0.92 ? (draw - 0.92) / 0.08 : 0)} />

      {/* Measurement label, centred on the cota */}
      {label && (
        <div
          style={{
            position: "absolute",
            left: horizontal ? `${(from + to) / 2}%` : `${offset + 6}%`,
            top: horizontal ? `${offset + 3.5}%` : `${(from + to) / 2}%`,
            transform: `translate(${horizontal ? "-50%" : "0"}, -50%) scale(${labelPop})`,
            background: "#FFFFFF",
            borderBottom: `6px solid ${accentColor}`,
            borderRadius: 14,
            padding: "16px 30px",
            boxShadow: "0 14px 40px rgba(0,0,0,0.3)",
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 800,
            fontSize: 46,
            color: textColor,
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </div>
      )}

      {/* Step marker, top-left */}
      {kicker && (
        <div
          style={{
            position: "absolute",
            left: 70,
            top: 70,
            opacity: kickerRise,
            transform: `translateY(${interpolate(kickerRise, [0, 1], [-18, 0])}px)`,
            background: accentColor,
            borderRadius: 10,
            padding: "14px 24px",
            fontFamily: "JetBrains Mono, monospace",
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: "0.10em",
            textTransform: "uppercase",
            color: "#FFFFFF",
          }}
        >
          {kicker}
        </div>
      )}

      {/* Exclusion caption, sat under the cross */}
      {excludeLabel && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            bottom: "8%",
            transform: `translateX(-50%) scale(${excludePop})`,
            background: excludeColor,
            borderRadius: 12,
            padding: "16px 34px",
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 800,
            fontSize: 48,
            letterSpacing: "0.02em",
            color: "#FFFFFF",
            boxShadow: "0 14px 40px rgba(0,0,0,0.32)",
          }}
        >
          {excludeLabel}
        </div>
      )}
    </AbsoluteFill>
  );
};
