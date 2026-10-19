/**
 * Calculate Drop Position Utility
 * Determines valid drop zones and insertion indices for drag-and-drop operations.
 *
 * Browser helpers: the functions take DOM elements (getBoundingClientRect) and
 * cursor coordinates, so import or copy them into client code; there is no CLI.
 */

// Calculate the drop position based on cursor position
function calculateDropPosition(cursor, elements, orientation = 'vertical') {
  if (!elements || elements.length === 0) {
    return { index: 0, closestElement: null };
  }

  const distances = elements.map((element, index) => {
    const rect = element.getBoundingClientRect();
    const center = orientation === 'vertical'
      ? rect.top + rect.height / 2
      : rect.left + rect.width / 2;

    const cursorPosition = orientation === 'vertical' ? cursor.y : cursor.x;
    const distance = Math.abs(center - cursorPosition);

    return { index, distance, center, element };
  });

  // Sort by distance to find closest element
  distances.sort((a, b) => a.distance - b.distance);
  const closest = distances[0];

  // Determine if cursor is before or after the closest element
  const cursorPos = orientation === 'vertical' ? cursor.y : cursor.x;
  const insertIndex = cursorPos < closest.center ? closest.index : closest.index + 1;

  return {
    index: Math.min(insertIndex, elements.length),
    closestElement: closest.element,
    distance: closest.distance,
  };
}

// Calculate drop zone for nested containers
function calculateDropZone(cursor, containers) {
  const zones = [];

  containers.forEach(container => {
    const rect = container.getBoundingClientRect();

    // Check if cursor is within container bounds
    if (cursor.x >= rect.left &&
        cursor.x <= rect.right &&
        cursor.y >= rect.top &&
        cursor.y <= rect.bottom) {

      // Calculate distance to center for priority
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const distance = Math.sqrt(
        Math.pow(cursor.x - centerX, 2) +
        Math.pow(cursor.y - centerY, 2)
      );

      zones.push({
        container,
        rect,
        distance,
        area: rect.width * rect.height,
      });
    }
  });

  if (zones.length === 0) return null;

  // Sort by smallest area first (most specific container)
  zones.sort((a, b) => a.area - b.area);

  return zones[0].container;
}

// Calculate grid position for 2D layouts
function calculateGridPosition(cursor, gridContainer, columns) {
  const rect = gridContainer.getBoundingClientRect();
  const relativeX = cursor.x - rect.left;
  const relativeY = cursor.y - rect.top;

  const columnWidth = rect.width / columns;
  const column = Math.floor(relativeX / columnWidth);
  const row = Math.floor(relativeY / (rect.height / Math.ceil(gridContainer.children.length / columns)));

  const index = row * columns + column;

  return {
    index: Math.min(index, gridContainer.children.length),
    row,
    column,
    position: { x: column * columnWidth, y: row * (rect.height / columns) },
  };
}

// Check if drop is valid based on rules
function validateDrop(draggedItem, dropTarget, rules = {}) {
  const {
    maxItems = Infinity,
    allowedTypes = [],
    rejectedTypes = [],
    customValidator = null,
  } = rules;

  // Check max items constraint
  if (dropTarget.children && dropTarget.children.length >= maxItems) {
    return { valid: false, reason: 'Container is full' };
  }

  // Check type constraints
  if (allowedTypes.length > 0 && !allowedTypes.includes(draggedItem.type)) {
    return { valid: false, reason: 'Item type not allowed' };
  }

  if (rejectedTypes.length > 0 && rejectedTypes.includes(draggedItem.type)) {
    return { valid: false, reason: 'Item type rejected' };
  }

  // Run custom validation if provided
  if (customValidator) {
    const customResult = customValidator(draggedItem, dropTarget);
    if (!customResult.valid) {
      return customResult;
    }
  }

  return { valid: true, reason: null };
}

// Calculate auto-scroll speed based on cursor position
function calculateAutoScroll(cursor, container, threshold = 50) {
  const rect = container.getBoundingClientRect();
  const scrollSpeed = { x: 0, y: 0 };
  const maxSpeed = 15;

  // Horizontal scrolling
  if (cursor.x < rect.left + threshold) {
    // Scroll left
    const distance = rect.left + threshold - cursor.x;
    scrollSpeed.x = -Math.min((distance / threshold) * maxSpeed, maxSpeed);
  } else if (cursor.x > rect.right - threshold) {
    // Scroll right
    const distance = cursor.x - (rect.right - threshold);
    scrollSpeed.x = Math.min((distance / threshold) * maxSpeed, maxSpeed);
  }

  // Vertical scrolling
  if (cursor.y < rect.top + threshold) {
    // Scroll up
    const distance = rect.top + threshold - cursor.y;
    scrollSpeed.y = -Math.min((distance / threshold) * maxSpeed, maxSpeed);
  } else if (cursor.y > rect.bottom - threshold) {
    // Scroll down
    const distance = cursor.y - (rect.bottom - threshold);
    scrollSpeed.y = Math.min((distance / threshold) * maxSpeed, maxSpeed);
  }

  return scrollSpeed;
}

// Find the nearest valid drop target
function findNearestDropTarget(cursor, dropTargets, maxDistance = 100) {
  let nearest = null;
  let minDistance = maxDistance;

  dropTargets.forEach(target => {
    const rect = target.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const distance = Math.sqrt(
      Math.pow(cursor.x - centerX, 2) +
      Math.pow(cursor.y - centerY, 2)
    );

    if (distance < minDistance) {
      minDistance = distance;
      nearest = target;
    }
  });

  return { target: nearest, distance: minDistance };
}

// Handle edge cases for drop position
function handleDropEdgeCases(dropPosition, container, item) {
  const adjustedPosition = { ...dropPosition };

  // Don't allow dropping item on itself
  if (item && container.contains(item)) {
    const itemIndex = Array.from(container.children).indexOf(item);
    if (adjustedPosition.index > itemIndex) {
      adjustedPosition.index--;
    }
  }

  // Ensure index is within bounds
  adjustedPosition.index = Math.max(0, Math.min(adjustedPosition.index, container.children.length));

  return adjustedPosition;
}

// Export functions for CommonJS/bundler use (no-op when loaded as a plain script)
if (typeof module !== 'undefined') module.exports = {
  calculateDropPosition,
  calculateDropZone,
  calculateGridPosition,
  validateDrop,
  calculateAutoScroll,
  findNearestDropTarget,
  handleDropEdgeCases,
};