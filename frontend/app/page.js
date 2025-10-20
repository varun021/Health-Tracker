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
import { HeartPulse } from "lucide-react";

// Mock data for the carousel
const features = [
  {
    title: "Find Doctors",
    description: "Search and connect with top-rated specialists near you.",
    imageSrc: "https://placehold.co/600x400/white/black?text=Doctor",
  },
  {
    title: "Explore Hospitals",
    description: "Discover trusted hospitals and clinics with advanced facilities.",
    imageSrc: "https://placehold.co/600x400/white/black?text=Hospital",
  },
  {
    title: "Order Medicines",
    description: "Get your prescriptions delivered to your doorstep quickly.",
    imageSrc: "https://placehold.co/600x400/white/black?text=Medicine",
  },
  {
    title: "Book Lab Tests",
    description: "Schedule diagnostic tests from certified labs with ease.",
    imageSrc: "https://placehold.co/600x400/white/black?text=Lab+Test",
  },
  {
    title: "Health Articles",
    description: "Read expert-written articles to stay informed and healthy.",
    imageSrc: "https://placehold.co/600x400/white/black?text=Articles",
  },
];

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

      {/* Features Carousel Section */}
      {/* <section className="w-full bg-secondary py-20">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold tracking-tighter sm:text-4xl">
              Everything You Need for Better Health
            </h3>
            <p className="max-w-xl mx-auto mt-4 text-muted-foreground">
              From finding the right doctor to getting medicines delivered, we've got you covered.
            </p>
          </div>
          <Carousel
            opts={{
              align: "start",
              loop: true,
            }}
            className="w-full max-w-5xl mx-auto"
          >
            <CarouselContent>
              {features.map((feature, index) => (
                <CarouselItem key={index} className="md:basis-1/2 lg:basis-1/3">
                  <div className="p-1">
                    <Card>
                      <CardContent className="flex flex-col items-center text-center p-6 aspect-square justify-center">
                        <Image
                          src={feature.imageSrc}
                          alt={feature.title}
                          width={400}
                          height={267}
                          className="rounded-md mb-4 object-cover"
                        />
                        <h4 className="text-xl font-semibold">{feature.title}</h4>
                        <p className="text-sm text-muted-foreground mt-2">
                          {feature.description}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="hidden sm:flex" />
            <CarouselNext className="hidden sm:flex" />
          </Carousel>
        </div>
      </section> */}

      {/* Footer */}
      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        <div className="container mx-auto px-4 md:px-6">
          © {new Date().getFullYear()} Health Tracker. All rights reserved.
        </div>
      </footer>
    </main>
  );
}