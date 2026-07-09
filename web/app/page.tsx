import { Nav } from "@/components/landing/Nav";
import { Hero } from "@/components/landing/Hero";
import { FeatureRow } from "@/components/landing/FeatureRow";
import { GraphSection } from "@/components/landing/GraphSection";
import { ProblemsWeHit } from "@/components/landing/ProblemsWeHit";
import { CodeShowcase } from "@/components/landing/CodeShowcase";
import { DemoTranscript } from "@/components/landing/DemoTranscript";
import { QualitativeBadges } from "@/components/landing/QualitativeBadges";
import { ClosingCta } from "@/components/landing/ClosingCta";
import { Footer } from "@/components/landing/Footer";
import { SunsetStripe } from "@/components/landing/SunsetStripe";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <Nav />
      <main className="flex-1">
        <Hero />
        <FeatureRow />
        <GraphSection />
        <ProblemsWeHit />
        <CodeShowcase />
        <DemoTranscript />
        <QualitativeBadges />
        <ClosingCta />
      </main>
      <Footer />
      <SunsetStripe />
    </div>
  );
}
