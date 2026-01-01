"use client";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-[#E8E0D5] shadow-sm">
      <div className="container mx-auto px-4 py-2 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-3">
          <img src="/logo.svg" alt="Eik Lab Logo" className="h-10 w-auto" />
        </Link>

        <nav className="hidden lg:flex items-center gap-8">
          <Link href="/academic_advisor" className="text-sm font-medium hover:text-gray-600">
            Digital studieveileder
          </Link>
          <Link href="/search" className="text-sm font-medium hover:text-gray-600">
            Emnesøk
          </Link>
          <Link href="/kontakt" className="text-sm font-medium hover:text-gray-600">
            Kontakt oss
          </Link>
        </nav>

        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="lg:hidden p-2 text-gray-900 hover:bg-gray-200 rounded-lg"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {isMenuOpen && (
        <nav className="lg:hidden border-t border-gray-300 mt-2">
          <div className="flex flex-col gap-4 p-4">
            <Link href="/academic_advisor">Digital studieveileder</Link>
            <Link href="/search">Emnesøk</Link>
            <Link href="/kontakt">Kontakt oss</Link>
          </div>
        </nav>
      )}
    </header>
  );
}