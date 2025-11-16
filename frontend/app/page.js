"use client";

import Image from "next/image";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { HeartPulse, Activity, FileText, TrendingUp, Database, Shield, Clock, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

const scaleIn = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.4 }
};

export default function Home() {
  const features = [
    {
      icon: Activity,
      title: "Symptom Analysis",
      description: "Submit your symptoms and get AI-powered insights into possible conditions with severity estimates."
    },
    {
      icon: TrendingUp,
      title: "Health Trends",
      description: "Track your health patterns over time and compare current status with previous periods."
    },
    {
      icon: FileText,
      title: "Medical Reports",
      description: "Generate and export professionally formatted health reports for your records or doctor visits."
    },
    {
      icon: Database,
      title: "Smart Learning",
      description: "Import datasets and train models to keep predictions accurate and personalized."
    }
  ];

  const benefits = [
    "Personalized health assessments",
    "Track lifestyle and medical history",
    "Identify potential conditions early",
    "Data-driven recommendations",
    "Export records anytime",
    "Privacy-focused platform"
  ];

  return (
    <main className="min-h-screen flex flex-col bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-lg bg-background/80 border-b">
        <div className="container mx-auto h-16 flex items-center justify-between px-4 md:px-6">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <HeartPulse className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-xl font-bold tracking-tight">
              Health Tracker
            </h1>
          </Link>
          <nav className="flex items-center gap-2">
            <Link
              href="/login"
              className={buttonVariants({ variant: "ghost" })}
            >
              Login
            </Link>
            <Link
              href="/signup"
              className={buttonVariants({ variant: "default" })}
            >
              Sign Up
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 md:px-6 py-20 md:py-32">
        <div className="max-w-5xl mx-auto">
          <motion.div 
            className="text-center mb-12"
            initial="initial"
            animate="animate"
            variants={staggerContainer}
          >
            <motion.div 
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6"
              variants={fadeInUp}
            >
              <Shield className="h-4 w-4" />
              Smart Health Assessment Platform
            </motion.div>
            <motion.h2 
              className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl mb-6 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent"
              variants={fadeInUp}
            >
              Understand Your Health,
              <br />
              <span className="text-primary">Take Control Today</span>
            </motion.h2>
            <motion.p 
              className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
              variants={fadeInUp}
            >
              Analyze symptoms, track patterns, and generate detailed medical reports. 
              Your comprehensive health companion powered by intelligent insights.
            </motion.p>

            <motion.div 
              className="flex flex-col sm:flex-row justify-center gap-4 mb-16"
              variants={fadeInUp}
            >
              <Link href="/login">
                <Button size="lg" className="w-full sm:w-auto text-base px-8">
                  Check Symptoms Now
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-base px-8">
                  Create Free Account
                </Button>
              </Link>
            </motion.div>
          </motion.div>

          {/* Stats */}
          <motion.div 
            className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-20"
            initial="initial"
            animate="animate"
            variants={staggerContainer}
          >
            {[
              { label: "Health Metrics", value: "50+" },
              { label: "Conditions Tracked", value: "200+" },
              { label: "Reports Generated", value: "10K+" },
              { label: "Accuracy Rate", value: "95%" }
            ].map((stat, i) => (
              <motion.div key={i} variants={scaleIn}>
                <Card className="border-2">
                  <CardContent className="p-6 text-center">
                    <div className="text-3xl font-bold text-primary mb-1">{stat.value}</div>
                    <div className="text-sm text-muted-foreground">{stat.label}</div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center mb-12">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need for Better Health
            </h3>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Comprehensive tools to monitor, analyze, and improve your wellbeing
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {features.map((feature, i) => (
              <Card key={i} className="border-2 hover:border-primary/50 transition-colors">
                <CardContent className="p-6">
                  <div className="p-3 rounded-lg bg-primary/10 w-fit mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h4 className="text-lg font-semibold mb-2">{feature.title}</h4>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
            <div>
              <h3 className="text-3xl md:text-4xl font-bold mb-6">
                Why Choose Health Tracker?
              </h3>
              <p className="text-muted-foreground mb-8">
                Get detailed insights into your health with our advanced symptom analysis system. 
                Track progress, spot trends, and make informed decisions about your wellbeing.
              </p>
              <div className="space-y-3">
                {benefits.map((benefit, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                    <span className="text-foreground">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <Card className="border-2">
              <CardContent className="p-8">
                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <Clock className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">Quick Assessment</div>
                      <div className="text-sm text-muted-foreground">Get results in minutes</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <Shield className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">Secure & Private</div>
                      <div className="text-sm text-muted-foreground">Your data is protected</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <FileText className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">Professional Reports</div>
                      <div className="text-sm text-muted-foreground">Export and share anytime</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 md:px-6 text-center">
          <h3 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Take Charge of Your Health?
          </h3>
          <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto">
            Join thousands of users who trust Health Tracker for their health monitoring needs
          </p>
          <Link href="/signup">
            <Button size="lg" variant="secondary" className="text-base px-8">
              Get Started Free
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 bg-muted/30">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-5 w-5 text-primary" />
              <span className="font-semibold">Health Tracker</span>
            </div>
            <div className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Health Tracker. Devloped By Rosie.
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}