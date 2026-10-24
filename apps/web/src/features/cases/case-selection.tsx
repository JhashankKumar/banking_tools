"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface CaseSelection {
  selectedPathIndex: number | null;
  selectedTransactionId: string | null;
  selectPath: (index: number | null) => void;
  selectTransaction: (id: string | null) => void;
  leftOpen: boolean;
  rightOpen: boolean;
  setLeftOpen: (open: boolean) => void;
  setRightOpen: (open: boolean) => void;
}

const Context = createContext<CaseSelection | null>(null);

/** Shared selection for the case page: graph, timeline, evidence, and limitations stay in sync. */
export function CaseSelectionProvider({
  pathCount,
  children,
}: {
  pathCount: number;
  children: ReactNode;
}) {
  // undefined = "not chosen yet": the first money path is selected by default once paths load.
  const [pathChoice, setPathChoice] = useState<number | null | undefined>(
    undefined,
  );
  const [selectedTransactionId, selectTransaction] = useState<string | null>(
    null,
  );
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const selectedPathIndex =
    pathChoice === undefined
      ? pathCount > 0
        ? 0
        : null
      : pathChoice !== null && pathChoice >= pathCount
        ? null
        : pathChoice;
  const value = useMemo(
    () => ({
      selectedPathIndex,
      selectedTransactionId,
      selectPath: setPathChoice,
      selectTransaction,
      leftOpen,
      rightOpen,
      setLeftOpen,
      setRightOpen,
    }),
    [selectedPathIndex, selectedTransactionId, leftOpen, rightOpen],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useCaseSelection(): CaseSelection {
  const value = useContext(Context);
  if (!value)
    throw new Error(
      "useCaseSelection must be used inside CaseSelectionProvider",
    );
  return value;
}
