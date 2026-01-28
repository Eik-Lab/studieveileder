"use client";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 shadow-sm w-screen">
      <div className="mx-auto px-4 py-4 flex justify-between items-center bg-gradient-to-br from-[#025C4F] to-[#0D3B34] w-full">
        <Link href="/" className="flex items-center gap-3 pl-10">
          <img src="/logo_3.svg" alt="Eik Lab Logo" className="h-10 w-auto" />
        </Link>

        <nav className="hidden lg:flex items-center gap-8 pr-4">
          <Link href="/academic_advisor" className="text-sm text-white font-medium hover:text-gray-600">
            Digital studieveileder
          </Link>
          <Link href="/search" className="text-sm text-white font-medium hover:text-gray-600">
            Emnesøk
          </Link>
          <Link href="/kontakt" className="text-sm text-white font-medium hover:text-gray-600">
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