"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Toaster } from "@/components/ui/toaster";
import { Dialog, DialogContent } from "@/components/ui/dialog";

// What we get back from the AI analysis
type Analysis = {
  mood: string;
  summary: string;
}

export default function Home() {
  // Store what the user types
  const [journalText, setJournalText] = useState("");
  
  // Track if we're saving
  const [isSaving, setIsSaving] = useState(false);
  
  // Store the AI analysis
  const [aiAnalysis, setAiAnalysis] = useState<Analysis | null>(null);
  
  // Store the saved journal entry
  const [savedJournal, setSavedJournal] = useState("");
  
  // Control showing the popup
  const [showPopup, setShowPopup] = useState(false);
  
  // For showing toast messages
  const { toast } = useToast();

  // Save the journal entry
  async function saveJournal() {
    // Don't save if empty
    if (!journalText.trim()) return;
    
    // Start saving
    setIsSaving(true);
    
    try {
      // Send to backend
      const response = await fetch("http://localhost:8000/journal-entry", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: journalText }),
      });

      // Check if it worked
      if (!response.ok) {
        throw new Error("Couldn't save journal");
      }

      const data = await response.json();

      // Everything worked!
      if (data.status === "success" && data.data.analysis) {
        setAiAnalysis(data.data.analysis);
        setSavedJournal(data.data.entry.entry);
        toast({
          title: "Saved!",
          description: "Your journal was saved and analyzed",
        });
      }
      // Saved but analysis failed
      else if (data.status === "partial_success") {
        setSavedJournal(data.data.entry.entry);
        toast({
          title: "Partially Saved",
          description: "Saved your journal but couldn't analyze it",
          variant: "destructive",
        });
      }

      // Clear the text box
      setJournalText("");
      
    } catch (error) {
      // Something went wrong
      toast({
        title: "Error",
        description: "Couldn't save your journal. Try again?",
        variant: "destructive",
      });
    }
    
    // Done saving
    setIsSaving(false);
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <Toaster />
      
      <main className="container mx-auto max-w-3xl">
        <h1 className="text-4xl font-bold mb-8 text-center">Check-In Digital Diary</h1>
        
        {/* Journal writing area */}
        <div className="space-y-6">
          <Card className="p-6">
            <div className="space-y-4">
              <Textarea
                placeholder="Write about your day..."
                className="min-h-[200px] resize-none"
                value={journalText}
                onChange={(e) => setJournalText(e.target.value)}
              />
              
              <div className="flex justify-end">
                <Button 
                  onClick={saveJournal}
                  disabled={isSaving || !journalText.trim()}
                >
                  {isSaving ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>
          </Card>

          {/* Show analysis if we have it */}
          {aiAnalysis && (
            <Card 
              className="cursor-pointer hover:bg-accent/50 transition-colors" 
              onClick={() => setShowPopup(true)}
            >
              <div className="p-6 space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Your Mood</h3>
                  <p className="text-muted-foreground">{aiAnalysis.mood}</p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Summary</h3>
                  <p className="text-muted-foreground">{aiAnalysis.summary}</p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </main>

      {/* Popup to show full journal entry */}
      <Dialog open={showPopup} onOpenChange={setShowPopup}>
        <DialogContent>
          <h2 className="font-bold text-lg mb-4">Your Journal Entry</h2>
          <p className="whitespace-pre-wrap">{savedJournal}</p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
