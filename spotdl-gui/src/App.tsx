import { useState } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import DownloadPage from './pages/DownloadPage';
import SettingsPage from './pages/SettingsPage';
import QueueList from './components/queue/QueueList';

function App() {
  const [activeTab, setActiveTab] = useState('download');

  const renderContent = () => {
    switch (activeTab) {
      case 'download':
        return <DownloadPage />;
      case 'queue':
        return <QueueList />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DownloadPage />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 max-w-7xl">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
