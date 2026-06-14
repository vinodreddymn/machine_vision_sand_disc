import { useCallback, useEffect, useState } from 'react';

import type {
  Alarm,
  DeviceStatus,
  HealthHistory,
  StartupDiagnostics,
  SystemHealth,
  ServiceStatus
} from '../types/systemHealth';

import {
  acknowledgeAlarm,
  getActiveAlarms,
  getDeviceStatus,
  getServiceStatus,
  getStartupDiagnostics,
  getSystemHealth,
  getSystemHistory
} from '../services/systemHealthService';

import { SystemOverview } from '../components/system/SystemOverview';
import { InfrastructurePanel } from '../components/system/InfrastructurePanel';
import { VisionHealthPanel } from '../components/system/VisionHealthPanel';
import { ProductionKpis } from '../components/system/ProductionKpis';
import { ProductionImpactPanel } from '../components/system/ProductionImpactPanel';

import { AlarmCommandCenter } from '../components/system/AlarmCommandCenter';
import { ServiceControlCenter } from '../components/system/ServiceControlCenter';

import { StartupTimeline } from '../components/system/StartupTimeline';
import { NotificationCenter } from '../components/system/NotificationCenter';

import { AnalyticsPanel } from '../components/system/AnalyticsPanel';
import { EventStream } from '../components/system/EventStream';

export function SystemHealthPage() {
  const [health, setHealth] =
    useState<SystemHealth | null>(null);

  const [devices, setDevices] =
    useState<DeviceStatus | null>(null);

  const [alarms, setAlarms] =
    useState<Alarm[]>([]);

  const [history, setHistory] =
    useState<HealthHistory[]>([]);

  const [services, setServices] =
    useState<Record<string, ServiceStatus>>({});

  const [diagnostics, setDiagnostics] =
    useState<StartupDiagnostics | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [notifStatus, setNotifStatus] =
    useState<{
      channels: Array<{ type: string }>;
    } | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [
        nextHealth,
        nextDevices,
        nextAlarms,
        nextHistory,
        nextDiagnostics
      ] = await Promise.all([
        getSystemHealth(),
        getDeviceStatus(),
        getActiveAlarms(),
        getSystemHistory(24, 200),
        getStartupDiagnostics().catch(
          () => null
        )
      ]);

      const nextServices =
        await getServiceStatus();

      try {
        const notifications =
          await fetch(
            '/api/system/notifications'
          ).then((r) => r.json());

        setNotifStatus(notifications);
      } catch {
        setNotifStatus(null);
      }

      setHealth(nextHealth);
      setDevices(nextDevices);
      setAlarms(nextAlarms);
      setHistory(nextHistory);
      setDiagnostics(nextDiagnostics);
      setServices(nextServices);

      setError(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : String(err)
      );
    }
  }, []);

  useEffect(() => {
    void refresh();

    const timer = window.setInterval(
      () => {
        void refresh();
      },
      3000
    );

    return () =>
      window.clearInterval(timer);
  }, [refresh]);

  const handleAcknowledge =
    useCallback(
      async (alarmId: number) => {
        await acknowledgeAlarm(alarmId);
        await refresh();
      },
      [refresh]
    );

    console.log({
      health,
      alarms,
      services,
      diagnostics
    });

  return (
    <div className="system-health-page">

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {/* =========================
          OPERATIONS OVERVIEW
      ========================= */}

      <SystemOverview
        health={health}
        alarms={alarms}
        services={services}
      />

      <ProductionImpactPanel
        health={health}
      />

      {/* =========================
          INFRASTRUCTURE
      ========================= */}

      <div className="sys-dual-layout">

        <InfrastructurePanel
          health={health}
          devices={devices}
        />

        <VisionHealthPanel
          health={health}
        />

      </div>

      {/* =========================
          PRODUCTION
      ========================= */}

      <ProductionKpis
        health={health}
      />

      {/* =========================
          OPERATIONS
      ========================= */}

      <AlarmCommandCenter
        alarms={alarms}
        onAcknowledge={
          handleAcknowledge
        }
      />

      <ServiceControlCenter
        services={services}
      />

      {/* =========================
          DIAGNOSTICS
      ========================= */}

      <div className="sys-dual-layout">

        <StartupTimeline
          diagnostics={
            diagnostics
          }
        />

        <NotificationCenter
          channels={
            notifStatus?.channels ??
            []
          }
        />

      </div>

      {/* =========================
          ANALYTICS
      ========================= */}

      <div className="sys-dual-layout">

        <AnalyticsPanel
          history={history}
        />

        <EventStream
          alarms={alarms}
          health={health}
        />

      </div>

    </div>
  );
}