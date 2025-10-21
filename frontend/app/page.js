// "use client";

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
import { HeartPulse } from "lucide-react";


export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="container mx-auto h-16 flex items-center justify-between border-b px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2">
          <HeartPulse className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold tracking-wide">
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
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 md:px-6 py-24">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-4xl font-extrabold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl mb-4">
            Your Health, <span className="text-muted-foreground">Our Priority</span>
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            A modern platform to check your symptoms, understand possible diseases,
            and get personalized health guidance — all in one place.
          </p>

          <div className="flex justify-center gap-4">
            <Link href="/login">
              <Button size="lg">Check Symptoms</Button>
            </Link>
            <Link href="/signup">
              <Button size="lg" variant="outline">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        <div className="container mx-auto px-4 md:px-6">
          © {new Date().getFullYear()} Health Tracker. All rights reserved.
        </div>
      </footer>
    </main>
  );
}