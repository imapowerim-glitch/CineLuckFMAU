"""
State Machine for CineLuck Camera Operations
Manages the finite state machine for camera operations
"""

import logging
import threading
import time
from enum import Enum
from typing import Callable, Dict, Optional

# Try to import PyQt6, fall back to basic implementation if not available
try:
    from PyQt6.QtCore import QObject, pyqtSignal
    PYQT_AVAILABLE = True
    
    class BaseStateMachine(QObject):
        """Base class with PyQt6 signals"""
        # Signals for state changes
        state_changed = pyqtSignal(object, object)  # new_state, old_state
        error_occurred = pyqtSignal(str)  # error_message
        
        def __init__(self):
            super().__init__()
        
        def emit_state_changed(self, new_state, old_state):
            self.state_changed.emit(new_state, old_state)
        
        def emit_error(self, error_message):
            self.error_occurred.emit(error_message)

except ImportError:
    PYQT_AVAILABLE = False
    
    class BaseStateMachine:
        """Fallback base class without PyQt6"""
        
        def __init__(self):
            self._signal_callbacks = {'state_changed': [], 'error_occurred': []}
        
        def connect_state_changed(self, callback):
            """Connect state changed callback"""
            self._signal_callbacks['state_changed'].append(callback)
        
        def connect_error_occurred(self, callback):
            """Connect error occurred callback"""
            self._signal_callbacks['error_occurred'].append(callback)
        
        def emit_state_changed(self, new_state, old_state):
            """Emit state changed signal"""
            for callback in self._signal_callbacks['state_changed']:
                try:
                    callback(new_state, old_state)
                except Exception as e:
                    logging.error(f"State changed callback error: {e}")
        
        def emit_error(self, error_message):
            """Emit error signal"""
            for callback in self._signal_callbacks['error_occurred']:
                try:
                    callback(error_message)
                except Exception as e:
                    logging.error(f"Error callback error: {e}")


class CameraState(Enum):
    """Camera operation states"""
    IDLE = "idle"
    PREVIEW = "preview"
    RECORDING = "recording"
    STOPPING = "stopping"
    ERROR = "error"


class StateMachine(BaseStateMachine):
    """
    Finite State Machine for camera operations
    Manages transitions between states with proper validation
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        CameraState.IDLE: [CameraState.PREVIEW, CameraState.ERROR],
        CameraState.PREVIEW: [CameraState.RECORDING, CameraState.IDLE, CameraState.ERROR],
        CameraState.RECORDING: [CameraState.STOPPING, CameraState.ERROR],
        CameraState.STOPPING: [CameraState.PREVIEW, CameraState.IDLE, CameraState.ERROR],
        CameraState.ERROR: [CameraState.IDLE, CameraState.PREVIEW]
    }
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._current_state = CameraState.IDLE
        self._lock = threading.RLock()
        self._watchdog_timer = None
        self._watchdog_timeout = 30  # seconds
        self._retry_count = 0
        self._max_retries = 3
        
        # State handlers
        self._state_handlers: Dict[CameraState, Callable] = {}
        self._transition_handlers: Dict[tuple, Callable] = {}
        
        self.logger.info("State machine initialized in IDLE state")
    
    @property
    def current_state(self) -> CameraState:
        """Get current state"""
        with self._lock:
            return self._current_state
    
    def is_state(self, state: CameraState) -> bool:
        """Check if current state matches given state"""
        return self.current_state == state
    
    def can_transition_to(self, new_state: CameraState) -> bool:
        """Check if transition to new state is valid"""
        with self._lock:
            return new_state in self.VALID_TRANSITIONS.get(self._current_state, [])
    
    def transition_to(self, new_state: CameraState, force: bool = False) -> bool:
        """
        Transition to new state
        
        Args:
            new_state: Target state
            force: Force transition even if not normally valid
            
        Returns:
            True if transition successful
        """
        with self._lock:
            old_state = self._current_state
            
            # Check if transition is valid
            if not force and not self.can_transition_to(new_state):
                self.logger.warning(
                    f"Invalid transition from {old_state.value} to {new_state.value}"
                )
                return False
            
            try:
                # Call transition handler if exists
                transition_key = (old_state, new_state)
                if transition_key in self._transition_handlers:
                    self._transition_handlers[transition_key]()
                
                # Update state
                self._current_state = new_state
                self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")
                
                # Reset retry count on successful transition
                if new_state != CameraState.ERROR:
                    self._retry_count = 0
                
                # Emit signal
                self.emit_state_changed(new_state, old_state)
                
                # Start watchdog for certain states
                self._start_watchdog()
                
                # Call state handler if exists
                if new_state in self._state_handlers:
                    try:
                        self._state_handlers[new_state]()
                    except Exception as e:
                        self.logger.error(f"State handler error for {new_state.value}: {e}")
                        self._handle_error(f"State handler error: {e}")
                        return False
                
                return True
                
            except Exception as e:
                self.logger.error(f"Transition error: {e}")
                self._handle_error(f"Transition error: {e}")
                return False
    
    def register_state_handler(self, state: CameraState, handler: Callable):
        """Register handler for entering a state"""
        self._state_handlers[state] = handler
        self.logger.debug(f"Registered state handler for {state.value}")
    
    def register_transition_handler(self, 
                                   from_state: CameraState, 
                                   to_state: CameraState, 
                                   handler: Callable):
        """Register handler for specific state transition"""
        transition_key = (from_state, to_state)
        self._transition_handlers[transition_key] = handler
        self.logger.debug(f"Registered transition handler: {from_state.value} -> {to_state.value}")
    
    def _handle_error(self, error_message: str):
        """Handle error state transition"""
        self.logger.error(f"Error: {error_message}")
        self.emit_error(error_message)
        
        # Increment retry count
        self._retry_count += 1
        
        # Transition to error state
        if self._current_state != CameraState.ERROR:
            self._current_state = CameraState.ERROR
            self.emit_state_changed(CameraState.ERROR, self._current_state)
        
        # Auto-recovery if retries available
        if self._retry_count <= self._max_retries:
            self.logger.info(f"Attempting auto-recovery (attempt {self._retry_count})")
            threading.Timer(2.0, self._attempt_recovery).start()
    
    def _attempt_recovery(self):
        """Attempt to recover from error state"""
        try:
            self.logger.info("Attempting recovery to IDLE state")
            self.transition_to(CameraState.IDLE, force=True)
        except Exception as e:
            self.logger.error(f"Recovery failed: {e}")
    
    def _start_watchdog(self):
        """Start watchdog timer for current state"""
        self._stop_watchdog()
        
        # Only start watchdog for certain states
        if self._current_state in [CameraState.PREVIEW, CameraState.RECORDING]:
            self._watchdog_timer = threading.Timer(
                self._watchdog_timeout, 
                self._watchdog_timeout_handler
            )
            self._watchdog_timer.start()
            self.logger.debug(f"Watchdog started for {self._current_state.value}")
    
    def _stop_watchdog(self):
        """Stop watchdog timer"""
        if self._watchdog_timer:
            self._watchdog_timer.cancel()
            self._watchdog_timer = None
    
    def _watchdog_timeout_handler(self):
        """Handle watchdog timeout"""
        self.logger.warning(f"Watchdog timeout in state {self._current_state.value}")
        
        if self._current_state == CameraState.PREVIEW:
            self._handle_error("Preview stalled - watchdog timeout")
        elif self._current_state == CameraState.RECORDING:
            self._handle_error("Recording stalled - watchdog timeout")
    
    def reset_watchdog(self):
        """Reset watchdog timer (call this to indicate state is healthy)"""
        if self._watchdog_timer:
            self._start_watchdog()  # Restart timer
    
    def force_idle(self):
        """Force transition to IDLE state (emergency stop)"""
        self.logger.warning("Forcing transition to IDLE state")
        self._stop_watchdog()
        with self._lock:
            old_state = self._current_state
            self._current_state = CameraState.IDLE
            self._retry_count = 0
            self.emit_state_changed(CameraState.IDLE, old_state)
    
    def get_state_duration(self) -> float:
        """Get how long we've been in current state (seconds)"""
        # This would need to be implemented with timestamp tracking
        # For now, return 0
        return 0.0
    
    def shutdown(self):
        """Clean shutdown of state machine"""
        self.logger.info("Shutting down state machine")
        self._stop_watchdog()
        self.force_idle()


# Safe Stop Manager - only available with PyQt6
if PYQT_AVAILABLE:
    class SafeStopManager(QObject):
        """
        Manages safe stop operations for recording
        Ensures proper encoder drainage and container finalization
        """
        
        stop_completed = pyqtSignal(bool)  # success
        stop_progress = pyqtSignal(str)    # status_message
        
        def __init__(self, state_machine: StateMachine):
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self.state_machine = state_machine
            self._stop_in_progress = False
        
        def is_stopping(self) -> bool:
            """Check if stop operation is in progress"""
            return self._stop_in_progress
        
        def safe_stop_recording(self, camera_manager, encoder_manager):
            """
            Perform safe stop of recording:
            1. Drain encoder
            2. Finalize container
            3. Wait on camera request
            4. Return to Preview
            """
            if self._stop_in_progress:
                self.logger.warning("Stop already in progress")
                return
            
            self._stop_in_progress = True
            self.logger.info("Starting safe stop sequence")
            
            # Run safe stop in separate thread
            stop_thread = threading.Thread(
                target=self._safe_stop_worker,
                args=(camera_manager, encoder_manager),
                daemon=True
            )
            stop_thread.start()
        
        def _safe_stop_worker(self, camera_manager, encoder_manager):
            """Worker thread for safe stop operation"""
            try:
                # Step 1: Signal recording stop
                self.stop_progress.emit("Stopping recording...")
                
                # Step 2: Drain encoder
                self.stop_progress.emit("Draining encoder...")
                if encoder_manager:
                    encoder_manager.drain_encoder()
                
                time.sleep(0.5)  # Brief pause for encoder
                
                # Step 3: Finalize container
                self.stop_progress.emit("Finalizing file...")
                if encoder_manager:
                    encoder_manager.finalize_recording()
                
                # Step 4: Wait on camera request
                self.stop_progress.emit("Finalizing camera...")
                if camera_manager:
                    camera_manager.stop_recording_safe()
                
                time.sleep(0.2)  # Brief pause for camera
                
                # Step 5: Transition to preview
                self.stop_progress.emit("Returning to preview...")
                success = self.state_machine.transition_to(CameraState.PREVIEW)
                
                if success:
                    self.logger.info("Safe stop completed successfully")
                    self.stop_progress.emit("Ready")
                else:
                    self.logger.error("Failed to return to preview state")
                    self.stop_progress.emit("Stop completed with errors")
                
                self.stop_completed.emit(success)
                
            except Exception as e:
                self.logger.error(f"Safe stop failed: {e}")
                self.stop_progress.emit(f"Stop failed: {e}")
                self.stop_completed.emit(False)
                
            finally:
                self._stop_in_progress = False

else:
    # Fallback SafeStopManager without PyQt6
    class SafeStopManager:
        """Fallback safe stop manager without PyQt6 signals"""
        
        def __init__(self, state_machine: StateMachine):
            self.logger = logging.getLogger(__name__)
            self.state_machine = state_machine
            self._stop_in_progress = False
            self._progress_callbacks = []
            self._completed_callbacks = []
        
        def connect_stop_progress(self, callback):
            """Connect progress callback"""
            self._progress_callbacks.append(callback)
        
        def connect_stop_completed(self, callback):
            """Connect completed callback"""
            self._completed_callbacks.append(callback)
        
        def emit_stop_progress(self, message):
            """Emit progress signal"""
            for callback in self._progress_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
        
        def emit_stop_completed(self, success):
            """Emit completed signal"""
            for callback in self._completed_callbacks:
                try:
                    callback(success)
                except Exception as e:
                    self.logger.error(f"Completed callback error: {e}")
        
        def is_stopping(self) -> bool:
            """Check if stop operation is in progress"""
            return self._stop_in_progress
        
        def safe_stop_recording(self, camera_manager, encoder_manager):
            """Perform safe stop (simplified version)"""
            if self._stop_in_progress:
                self.logger.warning("Stop already in progress")
                return
            
            self._stop_in_progress = True
            self.logger.info("Starting safe stop sequence")
            
            try:
                self.emit_stop_progress("Stopping recording...")
                time.sleep(0.5)
                
                self.emit_stop_progress("Finalizing...")
                success = self.state_machine.transition_to(CameraState.PREVIEW)
                
                self.emit_stop_completed(success)
                
            except Exception as e:
                self.logger.error(f"Safe stop failed: {e}")
                self.emit_stop_completed(False)
            finally:
                self._stop_in_progress = False