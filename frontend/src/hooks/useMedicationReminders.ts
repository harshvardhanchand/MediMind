import { useState, useEffect } from 'react';
import { useNotifications } from '../context/NotificationContext';
import { medicationServices } from '../api/services';
import { MedicationResponse, MedicationFrequency } from '../types/api';

interface MedicationReminder {
  medicationId: string;
  medicationName: string;
  dosage: string;
  times: Date[];
  notificationIds: string[];
  isEnabled: boolean;
}

interface UseMedicationRemindersReturn {
  reminders: MedicationReminder[];
  loading: boolean;
  enableReminder: (medicationId: string) => Promise<boolean>;
  disableReminder: (medicationId: string) => Promise<boolean>;
  updateReminderTimes: (medicationId: string, times: Date[]) => Promise<boolean>;
  refreshReminders: () => Promise<void>;
}

export const useMedicationReminders = (): UseMedicationRemindersReturn => {
  const [reminders, setReminders] = useState<MedicationReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const { scheduleMedicationReminder, cancelMedicationReminder } = useNotifications();

  const parseFrequencyToTimes = (frequency: MedicationFrequency, timeOfDay?: string[]): Date[] => {
    const times: Date[] = [];
    const now = new Date();
    
    // Default times if not specified
    const defaultTimes = {
      [MedicationFrequency.ONCE_DAILY]: ['08:00'],
      [MedicationFrequency.TWICE_DAILY]: ['08:00', '20:00'],
      [MedicationFrequency.THREE_TIMES_DAILY]: ['08:00', '14:00', '20:00'],
      [MedicationFrequency.FOUR_TIMES_DAILY]: ['08:00', '12:00', '16:00', '20:00'],
    };

    const timesToUse = timeOfDay || defaultTimes[frequency] || ['08:00'];

    timesToUse.forEach(time => {
      const [hours, minutes] = time.split(':').map(Number);
      const reminderTime = new Date(now);
      reminderTime.setHours(hours, minutes, 0, 0);
      
      // If the time has passed today, schedule for tomorrow
      if (reminderTime <= now) {
        reminderTime.setDate(reminderTime.getDate() + 1);
      }
      
      times.push(reminderTime);
    });

    return times;
  };

  const loadMedications = async (): Promise<MedicationResponse[]> => {
    try {
      const response = await medicationServices.getMedications({ 
        active_only: true, 
        limit: 100 
      });
      return response.data;
    } catch (error) {
      console.error('Failed to load medications:', error);
      return [];
    }
  };

  const refreshReminders = async () => {
    try {
      setLoading(true);
      const medications = await loadMedications();
      
      const medicationReminders: MedicationReminder[] = medications.map(med => {
        const times = parseFrequencyToTimes(med.frequency, med.time_of_day || undefined);
        
        return {
          medicationId: med.medication_id,
          medicationName: med.name,
          dosage: med.dosage || '',
          times,
          notificationIds: [], // Will be populated when reminders are enabled
          isEnabled: false, // Default to disabled, user must opt-in
        };
      });

      setReminders(medicationReminders);
    } catch (error) {
      console.error('Failed to refresh reminders:', error);
    } finally {
      setLoading(false);
    }
  };

  const enableReminder = async (medicationId: string): Promise<boolean> => {
    try {
      const reminder = reminders.find(r => r.medicationId === medicationId);
      if (!reminder) return false;

      const notificationIds: string[] = [];
      
      // Schedule a notification for each time
      for (const time of reminder.times) {
        const notificationId = await scheduleMedicationReminder(
          reminder.medicationName,
          reminder.dosage,
          time
        );
        
        if (notificationId) {
          notificationIds.push(notificationId);
        }
      }

      if (notificationIds.length > 0) {
        setReminders(prev => prev.map(r => 
          r.medicationId === medicationId 
            ? { ...r, isEnabled: true, notificationIds }
            : r
        ));
        
        console.log(`Enabled ${notificationIds.length} reminders for ${reminder.medicationName}`);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Failed to enable reminder:', error);
      return false;
    }
  };

  const disableReminder = async (medicationId: string): Promise<boolean> => {
    try {
      const reminder = reminders.find(r => r.medicationId === medicationId);
      if (!reminder) return false;

      // Cancel all scheduled notifications for this medication
      for (const notificationId of reminder.notificationIds) {
        await cancelMedicationReminder(notificationId);
      }

      setReminders(prev => prev.map(r => 
        r.medicationId === medicationId 
          ? { ...r, isEnabled: false, notificationIds: [] }
          : r
      ));

      console.log(`Disabled reminders for ${reminder.medicationName}`);
      return true;
    } catch (error) {
      console.error('Failed to disable reminder:', error);
      return false;
    }
  };

  const updateReminderTimes = async (medicationId: string, times: Date[]): Promise<boolean> => {
    try {
      const reminder = reminders.find(r => r.medicationId === medicationId);
      if (!reminder) return false;

      // If reminder is enabled, disable and re-enable with new times
      if (reminder.isEnabled) {
        await disableReminder(medicationId);
        
        // Update times
        setReminders(prev => prev.map(r => 
          r.medicationId === medicationId 
            ? { ...r, times }
            : r
        ));
        
        // Re-enable with new times
        return await enableReminder(medicationId);
      } else {
        // Just update times
        setReminders(prev => prev.map(r => 
          r.medicationId === medicationId 
            ? { ...r, times }
            : r
        ));
        return true;
      }
    } catch (error) {
      console.error('Failed to update reminder times:', error);
      return false;
    }
  };

  useEffect(() => {
    refreshReminders();
  }, []);

  return {
    reminders,
    loading,
    enableReminder,
    disableReminder,
    updateReminderTimes,
    refreshReminders,
  };
}; 