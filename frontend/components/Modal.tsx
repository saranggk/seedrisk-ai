"use client";

import { useEffect, useRef } from "react";
import type { MouseEvent, ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  label: string;
  children: ReactNode;
}

// Built on the native <dialog> element rather than a hand-rolled focus trap
// or a new dependency: showModal() gives a correct focus trap, Escape-to-close,
// and focus-return-to-trigger for free from the browser.
export function Modal({ open, onClose, label, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Callers typically pass an inline arrow (a new identity every render);
  // holding the latest one in a ref lets the listener effect below stay
  // mount-only instead of tearing down and resubscribing on every render.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    // Fires on Escape and on dialog.close() — keeps React state in sync
    // whenever the browser closes the dialog on its own.
    const handleClose = () => onCloseRef.current();
    dialog.addEventListener("close", handleClose);
    return () => dialog.removeEventListener("close", handleClose);
  }, []);

  // A click on the native ::backdrop dispatches its event with the dialog
  // itself as the target; a click on the dialog's content targets whatever
  // element is inside it. No wrapper div or stopPropagation needed.
  const handleClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      aria-label={label}
      onClick={handleClick}
      className="w-full max-w-2xl overflow-hidden rounded-2xl border-0 bg-surface p-0 shadow-2xl backdrop:bg-scrim"
    >
      {children}
    </dialog>
  );
}
