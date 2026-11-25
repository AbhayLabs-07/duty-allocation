import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

export const metadata = {
  title: "Smart Exam Duty Fairness & Allocation System",
  description: "Centralized examination duty allocation and fairness engine for engineering colleges",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex flex-col min-h-screen">
          <Topbar />
          <main className="flex-1 p-6 mt-16 max-w-7xl w-full mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
