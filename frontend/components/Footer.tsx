import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-white font-semibold mb-3">Eik Lab Studieveileder</h3>
            <p className="text-sm">
              Din digitale assistent for studier ved Norges miljø- og biovitenskapelige universitet.
            </p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-3">Kontakt</h3>
            <p className="text-sm">
              <br></br>
              <a
                href="mailto:frederic.ljosland.strand@nmbu.no"
                className="hover:text-white transition"
              >
                frederic.ljosland.strand@nmbu.no
              </a>
              <br></br>
              <a
                href="mailto:christopher.ljosland.strand@nmbu.no"
                className="hover:text-white transition"
              >christopher.ljosland.strand@nmbu.no</a>
            </p>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-6 text-sm text-center">
          <p>&copy; {new Date().getFullYear()} Eik Lab. Alle rettigheter reservert.</p>
        </div>
      </div>
    </footer>
  );
}
