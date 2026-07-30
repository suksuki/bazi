import React from "react";

export const hasNativeDisabledAttribute = (tag) =>
  /(?:^|\s)disabled(?:=|\s|>)/.test(tag);

function treeButtonElements(node, candidateRef, matches = []) {
  if (Array.isArray(node)) {
    for (const child of node) treeButtonElements(child, candidateRef, matches);
    return matches;
  }
  if (!React.isValidElement(node)) return matches;
  if (
    node.type === "button" &&
    node.props["data-candidate-ref"] === candidateRef
  ) {
    matches.push(node);
  }
  treeButtonElements(node.props.children, candidateRef, matches);
  return matches;
}

function guardedEvent(key = null) {
  const state = { defaultPrevented: false, propagationStopped: false };
  return {
    event: {
      ...(key === null ? {} : { key }),
      preventDefault: () => {
        state.defaultPrevented = true;
      },
      stopPropagation: () => {
        state.propagationStopped = true;
      },
    },
    state,
  };
}

function treeButton(scene, candidateRef, label, assertEqual) {
  const buttons = treeButtonElements(scene, candidateRef);
  assertEqual(`${label}-button-count`, buttons.length, 1);
  return buttons[0];
}

export function auditDreamGroveAccessibility({
  DreamGroveScene,
  assertEqual,
  availableProps,
  blockedCases,
  busyProps,
  candidateRef,
}) {
  const selectionCalls = [];
  const availableButton = treeButton(
    DreamGroveScene({
      ...availableProps,
      onSelect: (selectedRef) => selectionCalls.push(selectedRef),
    }),
    candidateRef,
    "available",
    assertEqual,
  );
  const availableClick = guardedEvent();
  availableButton.props.onClick(availableClick.event);
  assertEqual(
    "available-click-selects-once",
    selectionCalls.join(","),
    candidateRef,
  );
  assertEqual(
    "available-click-not-prevented",
    availableClick.state.defaultPrevented,
    false,
  );

  const busySelectionCalls = [];
  const busyButton = treeButton(
    DreamGroveScene({
      ...busyProps,
      onSelect: (selectedRef) => busySelectionCalls.push(selectedRef),
    }),
    candidateRef,
    "busy-available",
    assertEqual,
  );
  const busyClick = guardedEvent();
  busyButton.props.onClick(busyClick.event);
  assertEqual("busy-available-click-fails-closed", busySelectionCalls.length, 0);
  assertEqual("busy-click-prevented", busyClick.state.defaultPrevented, true);
  assertEqual(
    "busy-click-propagation-stopped",
    busyClick.state.propagationStopped,
    true,
  );

  for (const { expectedButtonCount = 1, label, props } of blockedCases) {
    const calls = [];
    const blockedButtons = treeButtonElements(
      DreamGroveScene({
        ...props,
        onSelect: (selectedRef) => calls.push(selectedRef),
      }),
      candidateRef,
    );
    assertEqual(
      `${label}-button-count`,
      blockedButtons.length,
      expectedButtonCount,
    );
    for (const [buttonIndex, blockedButton] of blockedButtons.entries()) {
      const buttonLabel =
        expectedButtonCount === 1 ? label : `${label}-${buttonIndex + 1}`;
      const click = guardedEvent();
      blockedButton.props.onClick(click.event);
      assertEqual(`${buttonLabel}-click-never-selects`, calls.length, 0);
      assertEqual(
        `${buttonLabel}-click-prevented`,
        click.state.defaultPrevented,
        true,
      );
      assertEqual(
        `${buttonLabel}-click-propagation-stopped`,
        click.state.propagationStopped,
        true,
      );
      for (const key of ["Enter", " "]) {
        const keyDown = guardedEvent(key);
        blockedButton.props.onKeyDown(keyDown.event);
        assertEqual(
          `${buttonLabel}-${JSON.stringify(key)}-prevented`,
          keyDown.state.defaultPrevented,
          true,
        );
        assertEqual(
          `${buttonLabel}-${JSON.stringify(key)}-propagation-stopped`,
          keyDown.state.propagationStopped,
          true,
        );
      }
      const navigationKey = guardedEvent("Tab");
      blockedButton.props.onKeyDown(navigationKey.event);
      assertEqual(
        `${buttonLabel}-tab-remains-available`,
        navigationKey.state.defaultPrevented,
        false,
      );
    }
  }

  return {
    blockedCardsKeyboardFocusable: true,
    blockedActivationGuarded: true,
    availableCardsSelectable: true,
  };
}
