interface SummaryMiniCardProps {
  title: string;
  value: string;
  caption?: string;
  progress?: number;
  progressTone?: "red" | "blue" | "green" | "white";
}

const progressClasses = {
  red: "bg-red-400",
  blue: "bg-blue-300",
  green: "bg-emerald-300",
  white: "bg-white",
};

export function SummaryMiniCard({
  title,
  value,
  caption,
  progress,
  progressTone = "white",
}: SummaryMiniCardProps) {
  return (
    <div className="rounded-xl bg-white/10 p-4 backdrop-blur-sm">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/60">{title}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
      {caption ? <p className="mt-2 text-[11px] font-bold text-emerald-300">{caption}</p> : null}
      {typeof progress === "number" ? (
        <div className="mt-3 h-1 w-full rounded-full bg-white/20">
          <div className={`h-1 rounded-full ${progressClasses[progressTone]}`} style={{ width: `${progress}%` }} />
        </div>
      ) : null}
    </div>
  );
}
